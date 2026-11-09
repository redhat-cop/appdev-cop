"""Unit tests for doc_scraping.py."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import typer

import doc_scraping


class TestIsSupportedDocument(unittest.TestCase):
    def test_supported_extensions(self):
        self.assertTrue(doc_scraping.is_supported_document(Path("report.pdf")))
        self.assertTrue(doc_scraping.is_supported_document(Path("notes.md")))
        self.assertTrue(doc_scraping.is_supported_document(Path("page.html")))

    def test_unsupported_extension(self):
        self.assertFalse(doc_scraping.is_supported_document(Path("binary.exe")))

    def test_tar_gz_archive(self):
        self.assertTrue(doc_scraping.is_supported_document(Path("archive.tar.gz")))


class TestCollectDocuments(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.data_dir = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_collects_supported_files_recursively(self):
        (self.data_dir / "doc.pdf").write_text("pdf", encoding="utf-8")
        nested = self.data_dir / "nested"
        nested.mkdir()
        (nested / "readme.md").write_text("# Title", encoding="utf-8")
        (nested / "skip.exe").write_text("bin", encoding="utf-8")

        documents = doc_scraping.collect_documents(self.data_dir)

        self.assertEqual(
            [path.name for path in documents],
            ["doc.pdf", "readme.md"],
        )

    def test_returns_empty_list_when_no_supported_files(self):
        (self.data_dir / "skip.exe").write_text("bin", encoding="utf-8")

        documents = doc_scraping.collect_documents(self.data_dir)

        self.assertEqual(documents, [])

    def test_raises_when_data_dir_missing(self):
        missing = self.data_dir / "missing"

        with self.assertRaises(typer.BadParameter):
            doc_scraping.collect_documents(missing)


class TestResolveOutputPath(unittest.TestCase):
    def test_preserves_relative_layout_from_data_dir(self):
        data_dir = Path("/tmp/data")
        src = data_dir / "nested" / "doc.pdf"
        out_dir = Path("/tmp/out")

        result = doc_scraping.resolve_output_path(src, out_dir, data_dir, "doc")

        self.assertEqual(result, out_dir / "nested" / "doc.md")


class TestChunkMarkdown(unittest.TestCase):
    def test_splits_long_text_into_multiple_chunks(self):
        text = "# Heading\n\n" + ("word " * 400)

        chunks = doc_scraping.chunk_markdown(text, chunk_size=120, overlap=20)

        self.assertGreater(len(chunks), 1)
        self.assertTrue(all(len(chunk) <= 120 for chunk in chunks))

    def test_keeps_short_text_in_single_chunk(self):
        text = "Short document body."

        chunks = doc_scraping.chunk_markdown(text)

        self.assertEqual(chunks, [text])


class TestConvertToMarkdown(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.out_dir = Path(self.temp_dir.name) / "out"

    def tearDown(self):
        self.temp_dir.cleanup()

    @patch("doc_scraping.DocumentConverter")
    def test_writes_markdown_for_local_file(self, mock_converter_cls):
        data_dir = Path(self.temp_dir.name) / "data"
        data_dir.mkdir()
        source = data_dir / "sample.md"
        source.write_text("# Sample", encoding="utf-8")

        mock_result = MagicMock()
        mock_result.document.export_to_markdown.return_value = "# Converted"
        mock_result.input.file.stem = "sample"
        mock_converter_cls.return_value.convert.return_value = mock_result

        results = doc_scraping.convert_to_markdown([source], self.out_dir, data_dir)

        self.assertEqual(len(results), 1)
        md_path = Path(results[0]["md_path"])
        self.assertTrue(md_path.exists())
        self.assertEqual(md_path.read_text(encoding="utf-8"), "# Converted")
        self.assertEqual(md_path, self.out_dir / "sample.md")

    @patch("doc_scraping.DocumentConverter")
    def test_continues_after_conversion_failure(self, mock_converter_cls):
        data_dir = Path(self.temp_dir.name) / "data"
        data_dir.mkdir()
        source = data_dir / "bad.pdf"
        source.write_text("pdf", encoding="utf-8")

        mock_converter_cls.return_value.convert.side_effect = RuntimeError("convert failed")

        results = doc_scraping.convert_to_markdown([source], self.out_dir, data_dir)

        self.assertEqual(results, [])


class TestBuildFaissIndexAndSearch(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.index_dir = Path(self.temp_dir.name) / "index"
        self.md_path = Path(self.temp_dir.name) / "doc.md"
        self.md_path.write_text(
            "Keycloak is an identity provider.\n\nIt supports SSO and OAuth2.",
            encoding="utf-8",
        )
        self.meta = [{"source": "doc.md", "md_path": str(self.md_path)}]

    def tearDown(self):
        self.temp_dir.cleanup()

    @patch("doc_scraping.SentenceTransformer")
    @patch("doc_scraping.faiss")
    def test_build_faiss_index_persists_index_files(self, mock_faiss, mock_st_model):
        import numpy as np

        mock_model = MagicMock()
        mock_model.encode.return_value = np.array([[0.1, 0.2, 0.3]], dtype="float32")
        mock_st_model.return_value = mock_model

        mock_index = MagicMock()
        mock_faiss.IndexFlatIP.return_value = mock_index

        doc_scraping.build_faiss_index(self.meta, self.index_dir)

        mock_faiss.write_index.assert_called_once()
        self.assertTrue((self.index_dir / "texts.json").exists())
        self.assertTrue((self.index_dir / "metadatas.json").exists())

    @patch("doc_scraping.SentenceTransformer")
    @patch("doc_scraping.faiss")
    def test_search_returns_ranked_results(self, mock_faiss, mock_st_model):
        import numpy as np

        texts = ["Keycloak is an identity provider.", "Unrelated content about databases."]
        metadatas = [
            {"source": "doc.md", "file": str(self.md_path), "chunk_id": 0},
            {"source": "other.md", "file": "other.md", "chunk_id": 0},
        ]
        (self.index_dir).mkdir(parents=True)
        (self.index_dir / "texts.json").write_text(json.dumps(texts), encoding="utf-8")
        (self.index_dir / "metadatas.json").write_text(
            json.dumps(metadatas), encoding="utf-8"
        )

        mock_index = MagicMock()
        mock_index.search.return_value = (
            np.array([[0.95, 0.10]]),
            np.array([[0, 1]]),
        )
        mock_faiss.read_index.return_value = mock_index

        mock_model = MagicMock()
        mock_model.encode.return_value = np.array([[0.1, 0.2, 0.3]], dtype="float32")
        mock_st_model.return_value = mock_model

        results = doc_scraping.search(self.index_dir, "identity provider", top_k=2)

        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["text"], texts[0])
        self.assertAlmostEqual(results[0]["score"], 0.95)


if __name__ == "__main__":
    unittest.main()
