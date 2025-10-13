"""
PubMed 200k RCT dataset processor.

This module provides utilities to process and prepare the PubMed 200k RCT dataset
for use in the document search RAG system.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Generator
from dataclasses import dataclass
import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class PubMedAbstract:
    """Represents a PubMed abstract with labeled sentences."""

    abstract_id: str
    sentences: List[str]
    labels: List[str]
    title: Optional[str] = None

    def to_dict(self) -> Dict:
        """Convert abstract to dictionary."""
        return {
            'abstract_id': self.abstract_id,
            'title': self.title,
            'sentences': self.sentences,
            'labels': self.labels,
            'full_text': ' '.join(self.sentences)
        }

    def to_structured_text(self) -> str:
        """Convert abstract to structured text with section headers."""
        structured_parts = []

        if self.title:
            structured_parts.append(f"Title: {self.title}\n")

        current_label = None
        current_section = []

        for sentence, label in zip(self.sentences, self.labels):
            if label != current_label:
                # Save previous section
                if current_section and current_label:
                    section_header = self._label_to_header(current_label)
                    structured_parts.append(f"\n{section_header}:\n")
                    structured_parts.append(' '.join(current_section))
                    structured_parts.append('\n')

                # Start new section
                current_label = label
                current_section = [sentence]
            else:
                current_section.append(sentence)

        # Add final section
        if current_section and current_label:
            section_header = self._label_to_header(current_label)
            structured_parts.append(f"\n{section_header}:\n")
            structured_parts.append(' '.join(current_section))

        return ''.join(structured_parts)

    @staticmethod
    def _label_to_header(label: str) -> str:
        """Convert label to readable section header."""
        label_map = {
            'BACKGROUND': 'Background',
            'OBJECTIVE': 'Objective',
            'METHODS': 'Methods',
            'RESULTS': 'Results',
            'CONCLUSIONS': 'Conclusions'
        }
        return label_map.get(label.upper(), label.title())


class PubMedDatasetProcessor:
    """Process PubMed 200k RCT dataset for document search."""

    def __init__(self, dataset_dir: Path):
        """
        Initialize the processor with dataset directory.

        Args:
            dataset_dir: Path to the PubMed 200k RCT dataset directory
        """
        self.dataset_dir = Path(dataset_dir)
        self.label_map = {
            'BACKGROUND': 0,
            'OBJECTIVE': 1,
            'METHODS': 2,
            'RESULTS': 3,
            'CONCLUSIONS': 4
        }
        self.reverse_label_map = {v: k for k, v in self.label_map.items()}

    def parse_dataset_file(self, file_path: Path) -> Generator[PubMedAbstract, None, None]:
        """
        Parse a dataset file and yield PubMedAbstract objects.

        The PubMed 200k RCT dataset format:
        - Each line is a JSON object
        - Contains 'abstract_id', 'sentences', and 'labels' fields

        Args:
            file_path: Path to the dataset file (train.txt, dev.txt, or test.txt)

        Yields:
            PubMedAbstract objects
        """
        if not file_path.exists():
            logger.error(f"Dataset file not found: {file_path}")
            return

        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                try:
                    # Parse JSON line
                    data = json.loads(line.strip())

                    # Extract fields
                    abstract_id = data.get('abstract_id', f'abstract_{line_num}')
                    sentences = data.get('sentences', [])
                    labels = data.get('labels', [])

                    # Convert numeric labels to text if needed
                    if labels and isinstance(labels[0], int):
                        labels = [self.reverse_label_map.get(l, 'UNKNOWN') for l in labels]

                    yield PubMedAbstract(
                        abstract_id=abstract_id,
                        sentences=sentences,
                        labels=labels
                    )

                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse line {line_num}: {e}")
                    continue
                except Exception as e:
                    logger.warning(f"Error processing line {line_num}: {e}")
                    continue

    def process_to_documents(
        self,
        split: str = 'train',
        max_documents: Optional[int] = None,
        output_format: str = 'structured'
    ) -> List[Dict]:
        """
        Process dataset split into document format for indexing.

        Args:
            split: Dataset split to process ('train', 'dev', or 'test')
            max_documents: Maximum number of documents to process
            output_format: 'structured' for section-based text, 'flat' for plain text

        Returns:
            List of document dictionaries ready for indexing
        """
        # Find the dataset file
        file_name = f"{split}.txt"
        file_paths = list(self.dataset_dir.rglob(file_name))

        if not file_paths:
            logger.error(f"Could not find {file_name} in {self.dataset_dir}")
            return []

        file_path = file_paths[0]
        logger.info(f"Processing {file_path}")

        documents = []

        for idx, abstract in enumerate(self.parse_dataset_file(file_path)):
            if max_documents and idx >= max_documents:
                break

            # Create document
            doc = {
                'id': abstract.abstract_id,
                'source': f'pubmed_200k_rct_{split}',
                'metadata': {
                    'split': split,
                    'num_sentences': len(abstract.sentences),
                    'labels': list(set(abstract.labels))
                }
            }

            # Add text content based on format
            if output_format == 'structured':
                doc['content'] = abstract.to_structured_text()
            else:
                doc['content'] = ' '.join(abstract.sentences)

            # Add individual sections as metadata
            sections = self._extract_sections(abstract)
            doc['metadata'].update(sections)

            documents.append(doc)

        logger.info(f"Processed {len(documents)} documents from {split} split")
        return documents

    def _extract_sections(self, abstract: PubMedAbstract) -> Dict[str, str]:
        """Extract text for each section label."""
        sections = {}

        for label in set(abstract.labels):
            # Get all sentences with this label
            label_sentences = [
                sent for sent, l in zip(abstract.sentences, abstract.labels)
                if l == label
            ]

            if label_sentences:
                section_key = f"section_{label.lower()}"
                sections[section_key] = ' '.join(label_sentences)

        return sections

    def create_training_dataset(
        self,
        output_path: Path,
        splits: List[str] = ['train', 'dev', 'test'],
        max_per_split: Optional[int] = None
    ):
        """
        Create a processed dataset file for training or evaluation.

        Args:
            output_path: Path to save the processed dataset
            splits: List of splits to include
            max_per_split: Maximum documents per split
        """
        all_documents = []

        for split in splits:
            documents = self.process_to_documents(
                split=split,
                max_documents=max_per_split,
                output_format='structured'
            )
            all_documents.extend(documents)

        # Save as JSON Lines format
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            for doc in all_documents:
                f.write(json.dumps(doc) + '\n')

        logger.info(f"Saved {len(all_documents)} documents to {output_path}")

    def get_dataset_statistics(self) -> Dict:
        """
        Get statistics about the dataset.

        Returns:
            Dictionary with dataset statistics
        """
        stats = {
            'splits': {},
            'total': {
                'abstracts': 0,
                'sentences': 0
            }
        }

        for split in ['train', 'dev', 'test']:
            file_name = f"{split}.txt"
            file_paths = list(self.dataset_dir.rglob(file_name))

            if not file_paths:
                continue

            file_path = file_paths[0]

            split_stats = {
                'abstracts': 0,
                'sentences': 0,
                'label_distribution': {}
            }

            for abstract in self.parse_dataset_file(file_path):
                split_stats['abstracts'] += 1
                split_stats['sentences'] += len(abstract.sentences)

                # Count label distribution
                for label in abstract.labels:
                    if label not in split_stats['label_distribution']:
                        split_stats['label_distribution'][label] = 0
                    split_stats['label_distribution'][label] += 1

            stats['splits'][split] = split_stats
            stats['total']['abstracts'] += split_stats['abstracts']
            stats['total']['sentences'] += split_stats['sentences']

        return stats


def prepare_pubmed_for_rag(
    dataset_dir: Path,
    output_dir: Path,
    max_documents: Optional[int] = None
) -> Path:
    """
    Prepare PubMed 200k RCT dataset for RAG system.

    Args:
        dataset_dir: Path to the downloaded dataset
        output_dir: Directory to save processed documents
        max_documents: Maximum number of documents to process (for testing)

    Returns:
        Path to the processed dataset file
    """
    processor = PubMedDatasetProcessor(dataset_dir)

    # Get statistics
    stats = processor.get_dataset_statistics()

    print("\n" + "="*50)
    print("Dataset Statistics")
    print("="*50)

    for split, split_stats in stats['splits'].items():
        print(f"\n{split.upper()} Split:")
        print(f"  Abstracts: {split_stats['abstracts']:,}")
        print(f"  Sentences: {split_stats['sentences']:,}")

        if split_stats['label_distribution']:
            print("  Label Distribution:")
            for label, count in sorted(split_stats['label_distribution'].items()):
                print(f"    {label}: {count:,}")

    print(f"\nTotal Abstracts: {stats['total']['abstracts']:,}")
    print(f"Total Sentences: {stats['total']['sentences']:,}")
    print("="*50)

    # Process dataset
    output_file = output_dir / 'pubmed_200k_rct_processed.jsonl'

    processor.create_training_dataset(
        output_path=output_file,
        splits=['train', 'dev', 'test'],
        max_per_split=max_documents
    )

    return output_file


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Process PubMed 200k RCT dataset for RAG"
    )
    parser.add_argument(
        '--dataset-dir',
        type=Path,
        default=Path('./data/pubmed_200k_rct'),
        help='Path to the dataset directory'
    )
    parser.add_argument(
        '--output-dir',
        type=Path,
        default=Path('./data/processed'),
        help='Output directory for processed data'
    )
    parser.add_argument(
        '--max-documents',
        type=int,
        help='Maximum number of documents to process (for testing)'
    )

    args = parser.parse_args()

    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Process the dataset
    output_file = prepare_pubmed_for_rag(
        dataset_dir=args.dataset_dir,
        output_dir=args.output_dir,
        max_documents=args.max_documents
    )

    print(f"\nProcessed dataset saved to: {output_file}")