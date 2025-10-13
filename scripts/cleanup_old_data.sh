#!/bin/bash

# Script to clean up old PubMed data after migration

echo "======================================"
echo "PubMed Data Cleanup"
echo "======================================"
echo ""
echo "New data location: /Users/sankar/sankar/courses/llm/data/pubmed/"
echo ""
echo "Old data directories to be removed:"
echo ""

# Show old directories and their sizes
for dir in data/pubmed_200k_rct data/pubmed_20k_rct data/pubmed_rct_sample data/processed; do
    if [ -d "$dir" ]; then
        size=$(du -sh "$dir" 2>/dev/null | cut -f1)
        echo "  - $dir ($size)"
    fi
done

echo ""
echo "Total space to be freed:"
du -sh data/pubmed_* data/processed/ 2>/dev/null | awk '{sum+=$1} END {print sum "M"}'

echo ""
echo "======================================"
echo "⚠️  WARNING: This will permanently delete the old data!"
echo "The data has been copied to: /Users/sankar/sankar/courses/llm/data/pubmed/"
echo "======================================"
echo ""
read -p "Are you sure you want to delete the old directories? (type 'yes' to confirm): " response

if [ "$response" == "yes" ]; then
    echo ""
    echo "Removing old directories..."

    # Remove old directories
    rm -rf data/pubmed_200k_rct
    echo "  ✓ Removed data/pubmed_200k_rct"

    rm -rf data/pubmed_20k_rct
    echo "  ✓ Removed data/pubmed_20k_rct"

    rm -rf data/pubmed_rct_sample
    echo "  ✓ Removed data/pubmed_rct_sample"

    rm -rf data/processed
    echo "  ✓ Removed data/processed"

    echo ""
    echo "✅ Cleanup complete!"
    echo ""
    echo "The symlink 'data/pubmed' still points to the new location:"
    ls -la data/pubmed
else
    echo ""
    echo "Cleanup cancelled. No files were deleted."
fi