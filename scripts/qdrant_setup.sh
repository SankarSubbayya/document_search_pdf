#!/bin/bash

# Qdrant Docker Setup Script
# This script helps manage Qdrant vector database in Docker

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check if Docker is installed
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose."
        exit 1
    fi

    print_status "Docker and Docker Compose are installed."
}

# Start Qdrant container
start_qdrant() {
    print_status "Starting Qdrant container..."

    # Use docker compose or docker-compose based on availability
    if docker compose version &> /dev/null; then
        docker compose up -d qdrant
    else
        docker-compose up -d qdrant
    fi

    # Wait for Qdrant to be healthy
    print_status "Waiting for Qdrant to be ready..."
    sleep 5

    # Check health
    max_attempts=30
    attempt=0

    while [ $attempt -lt $max_attempts ]; do
        if curl -s -f http://localhost:6333/health > /dev/null 2>&1; then
            print_status "Qdrant is healthy and ready!"
            break
        fi

        attempt=$((attempt + 1))
        if [ $attempt -eq $max_attempts ]; then
            print_error "Qdrant failed to start properly after $max_attempts attempts."
            exit 1
        fi

        echo -n "."
        sleep 2
    done

    echo ""
    print_status "Qdrant is running at:"
    echo "  - REST API: http://localhost:6333"
    echo "  - gRPC API: localhost:6334"
    echo "  - Dashboard: http://localhost:6333/dashboard"
}

# Stop Qdrant container
stop_qdrant() {
    print_status "Stopping Qdrant container..."

    if docker compose version &> /dev/null; then
        docker compose stop qdrant
    else
        docker-compose stop qdrant
    fi

    print_status "Qdrant stopped."
}

# Remove Qdrant container
remove_qdrant() {
    print_warning "This will remove the Qdrant container (data will be preserved in volumes)."
    read -p "Are you sure? (y/N) " -n 1 -r
    echo

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        if docker compose version &> /dev/null; then
            docker compose rm -f qdrant
        else
            docker-compose rm -f qdrant
        fi
        print_status "Qdrant container removed."
    else
        print_status "Operation cancelled."
    fi
}

# Check Qdrant status
check_status() {
    if docker ps | grep -q qdrant; then
        print_status "Qdrant is running."

        # Check health endpoint
        if curl -s -f http://localhost:6333/health > /dev/null 2>&1; then
            print_status "Qdrant health check: PASSED"

            # Get collections info
            collections=$(curl -s http://localhost:6333/collections | python3 -m json.tool 2>/dev/null || echo "{}")
            if [ "$collections" != "{}" ]; then
                echo ""
                print_status "Collections information:"
                echo "$collections" | python3 -c "
import json
import sys
data = json.load(sys.stdin)
if 'result' in data and 'collections' in data['result']:
    collections = data['result']['collections']
    if collections:
        for coll in collections:
            print(f\"  - {coll['name']}\")
    else:
        print('  No collections found.')
"
            fi
        else
            print_warning "Qdrant is running but health check failed."
        fi
    else
        print_warning "Qdrant is not running."
    fi
}

# View Qdrant logs
view_logs() {
    print_status "Showing Qdrant logs (press Ctrl+C to exit)..."
    docker logs -f qdrant
}

# Backup Qdrant data
backup_data() {
    timestamp=$(date +%Y%m%d_%H%M%S)
    backup_dir="backups/qdrant_backup_$timestamp"

    print_status "Creating backup in $backup_dir..."
    mkdir -p "$backup_dir"

    # Copy Qdrant storage
    if [ -d "qdrant_storage" ]; then
        cp -r qdrant_storage "$backup_dir/"
        print_status "Backup created successfully at: $backup_dir"
    else
        print_error "Qdrant storage directory not found."
        exit 1
    fi
}

# Restore Qdrant data
restore_data() {
    if [ -z "$1" ]; then
        print_error "Please provide backup directory path."
        echo "Usage: $0 restore <backup_directory>"
        exit 1
    fi

    backup_dir="$1"

    if [ ! -d "$backup_dir/qdrant_storage" ]; then
        print_error "Invalid backup directory: $backup_dir"
        exit 1
    fi

    print_warning "This will replace current Qdrant data with backup from $backup_dir"
    read -p "Are you sure? (y/N) " -n 1 -r
    echo

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # Stop Qdrant first
        stop_qdrant

        # Backup current data
        if [ -d "qdrant_storage" ]; then
            mv qdrant_storage "qdrant_storage.old_$(date +%Y%m%d_%H%M%S)"
        fi

        # Restore backup
        cp -r "$backup_dir/qdrant_storage" .

        # Start Qdrant
        start_qdrant

        print_status "Data restored successfully."
    else
        print_status "Operation cancelled."
    fi
}

# Clean up everything
clean_all() {
    print_warning "This will remove Qdrant container AND all data!"
    read -p "Are you sure? Type 'yes' to confirm: " -r

    if [ "$REPLY" == "yes" ]; then
        if docker compose version &> /dev/null; then
            docker compose down -v
        else
            docker-compose down -v
        fi

        rm -rf qdrant_storage
        print_status "Qdrant and all data removed."
    else
        print_status "Operation cancelled."
    fi
}

# Main menu
show_menu() {
    echo ""
    echo "==================================="
    echo "    Qdrant Docker Manager"
    echo "==================================="
    echo "1) Start Qdrant"
    echo "2) Stop Qdrant"
    echo "3) Check Status"
    echo "4) View Logs"
    echo "5) Backup Data"
    echo "6) Restore Data"
    echo "7) Remove Container"
    echo "8) Clean All (Remove everything)"
    echo "9) Exit"
    echo "==================================="
}

# Main script
main() {
    # Check Docker first
    check_docker

    # If command provided, execute it
    if [ $# -gt 0 ]; then
        case "$1" in
            start)
                start_qdrant
                ;;
            stop)
                stop_qdrant
                ;;
            status)
                check_status
                ;;
            logs)
                view_logs
                ;;
            backup)
                backup_data
                ;;
            restore)
                restore_data "$2"
                ;;
            remove)
                remove_qdrant
                ;;
            clean)
                clean_all
                ;;
            *)
                print_error "Unknown command: $1"
                echo "Usage: $0 {start|stop|status|logs|backup|restore|remove|clean}"
                exit 1
                ;;
        esac
    else
        # Interactive menu
        while true; do
            show_menu
            read -p "Select an option: " choice

            case $choice in
                1)
                    start_qdrant
                    ;;
                2)
                    stop_qdrant
                    ;;
                3)
                    check_status
                    ;;
                4)
                    view_logs
                    ;;
                5)
                    backup_data
                    ;;
                6)
                    read -p "Enter backup directory path: " backup_path
                    restore_data "$backup_path"
                    ;;
                7)
                    remove_qdrant
                    ;;
                8)
                    clean_all
                    ;;
                9)
                    print_status "Goodbye!"
                    exit 0
                    ;;
                *)
                    print_error "Invalid option. Please select 1-9."
                    ;;
            esac

            echo ""
            read -p "Press Enter to continue..."
        done
    fi
}

# Run main function
main "$@"