"""
PubMed 200k RCT dataset processor for tab-separated format.

This module processes the PubMed 200k RCT dataset that uses tab-separated format
with abstract IDs starting with ### and label-text pairs.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Generator
from dataclasses import dataclass
import json

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


class PubMedDatasetProcessorTSV:
    """Process PubMed 200k RCT dataset in tab-separated format."""

    def __init__(self, dataset_dir: Path):
        """
        Initialize the processor with dataset directory.

        Args:
            dataset_dir: Path to the PubMed 200k RCT dataset directory
        """
        self.dataset_dir = Path(dataset_dir)

    def parse_dataset_file(self, file_path: Path) -> Generator[PubMedAbstract, None, None]:
        """
        Parse a dataset file in tab-separated format and yield PubMedAbstract objects.

        The format:
        - Lines starting with ### contain the abstract ID
        - Following lines have LABEL<tab>text format

        Args:
            file_path: Path to the dataset file (train.txt, dev.txt, or test.txt)

        Yields:
            PubMedAbstract objects
        """
        if not file_path.exists():
            logger.error(f"Dataset file not found: {file_path}")
            return

        current_abstract = None
        current_sentences = []
        current_labels = []

        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()

                if not line:
                    continue

                # Check if this is a new abstract
                if line.startswith('###'):
                    # Save previous abstract if exists
                    if current_abstract and current_sentences:
                        yield PubMedAbstract(
                            abstract_id=current_abstract,
                            sentences=current_sentences,
                            labels=current_labels
                        )

                    # Start new abstract
                    current_abstract = line[3:].strip()  # Remove ### prefix
                    current_sentences = []
                    current_labels = []

                elif '\t' in line:
                    # Parse label and text
                    parts = line.split('\t', 1)
                    if len(parts) == 2:
                        label, text = parts
                        current_labels.append(label.strip())
                        current_sentences.append(text.strip())

        # Don't forget the last abstract
        if current_abstract and current_sentences:
            yield PubMedAbstract(
                abstract_id=current_abstract,
                sentences=current_sentences,
                labels=current_labels
            )

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
        file_path = self.dataset_dir / file_name

        if not file_path.exists():
            logger.error(f"Could not find {file_name} in {self.dataset_dir}")
            return []

        logger.info(f"Processing {file_path}")

        documents = []

        for idx, abstract in enumerate(self.parse_dataset_file(file_path)):
            if max_documents and idx >= max_documents:
                break

            # Create document
            doc = {
                'id': f"pubmed_{abstract.abstract_id}",
                'source': f'pubmed_200k_rct_{split}',
                'metadata': {
                    'split': split,
                    'abstract_id': abstract.abstract_id,
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

            if (idx + 1) % 1000 == 0:
                logger.info(f"Processed {idx + 1} documents...")

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
            file_path = self.dataset_dir / f"{split}.txt"

            if not file_path.exists():
                continue

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


def process_pubmed_200k_dataset(
    dataset_dir: Path,
    output_dir: Path,
    max_documents: Optional[int] = None
) -> Path:
    """
    Process PubMed 200k RCT dataset in TSV format for RAG system.

    Args:
        dataset_dir: Path to the downloaded dataset
        output_dir: Directory to save processed documents
        max_documents: Maximum number of documents to process (for testing)

    Returns:
        Path to the processed dataset file
    """
    processor = PubMedDatasetProcessorTSV(dataset_dir)

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
        description="Process PubMed 200k RCT dataset (TSV format) for RAG"
    )
    parser.add_argument(
        '--dataset-dir',
        type=Path,
        default=Path('/Users/sankar/sankar/courses/llm/data/pubmed/raw'),
        help='Path to the dataset directory'
    )
    parser.add_argument(
        '--output-dir',
        type=Path,
        default=Path('/Users/sankar/sankar/courses/llm/data/pubmed/processed'),
        help='Output directory for processed data'
    )
    parser.add_argument(
        '--max-documents',
        type=int,
        help='Maximum number of documents to process per split (for testing)'
    )

    args = parser.parse_args()

    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Process the dataset
    output_file = process_pubmed_200k_dataset(
        dataset_dir=args.dataset_dir,
        output_dir=args.output_dir,
        max_documents=args.max_documents
    )

    print(f"\nProcessed dataset saved to: {output_file}")