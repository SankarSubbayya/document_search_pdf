# Project Structure

```
document_search_pdf/
├── apps/                      # Main applications
│   ├── pdf_manager_app.py    # PDF management with separate collection
│   ├── streamlit_pubmed_app.py # PubMed search app
│   └── streamlit_upload_app.py # Upload + PubMed search app
│
├── src/                       # Source code
│   ├── config/               # Configuration modules
│   ├── core/                 # Core functionality
│   ├── processing/           # Document processing
│   │   ├── document_processor.py
│   │   └── pdf_processor.py
│   ├── retrieval/            # RAG and retrieval
│   └── storage/              # Storage and database
│
├── tests/                     # Test files
│   ├── conftest.py           # Test configuration
│   ├── test_pdf_processor.py # Unit tests
│   ├── test_vector_operations.py # Integration tests
│   └── test_streamlit_app.py # E2E tests
│
├── scripts/                   # Utility scripts
│   ├── runners/              # Run and launch scripts
│   │   ├── run_pdf_manager.sh
│   │   ├── run_tests.sh
│   │   └── test_with_uv.sh
│   ├── utils/                # Utility scripts
│   └── index_pdfs.py         # PDF indexing script
│
├── config/                    # Configuration files
│   ├── config.yaml           # Main configuration
│   └── pdf_config.yaml       # PDF-specific config
│
├── docs/                      # Documentation
│   ├── README.md             # Main documentation
│   ├── TESTING.md            # Testing guide
│   └── archive_readmes/      # Archived documentation
│
├── archive/                   # Archived old code
│
├── data/                      # Data directories
│   ├── pdf_uploads/          # Uploaded PDFs
│   └── test_documents/       # Test documents
│
├── requirements.txt          # Python dependencies
├── pyproject.toml           # Project configuration
├── docker-compose.yml       # Docker configuration
└── README.md                # Main README
```
