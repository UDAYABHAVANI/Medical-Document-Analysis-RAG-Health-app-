# 🩺 Medical Document Analysis (RAG System)

An intelligent, secure, and fully local web application that allows users to query complex medical documents (PDFs and Excel files) using Natural Language. Built with a Retrieval-Augmented Generation (RAG) architecture, this system ensures high accuracy, prevents AI hallucinations, and keeps sensitive medical data 100% private.

## ✨ Key Features

* **Private & Secure AI:** Uses local Large Language Models (LLMs) via Ollama, ensuring sensitive medical documents never leave the local machine.
* **Smart RAG Pipeline:** Parses documents, chunks text, and generates high-dimensional vector embeddings stored in **ChromaDB** for semantic search.
* **Multi-Page Citations:** Answers include exact source tracking, providing users with the specific PDF or Excel page numbers used by the AI to formulate the response.
* **Dual-Layer Caching:** Integrates an **SQL Server** database to cache exact-match questions, delivering instant answers for repeated queries and reducing AI latency to zero.
* **Interactive Dashboard:** Features a clean, responsive UI built with Flask and Bootstrap to track user history, manage uploaded files, and view past Q&A sessions.

## 🛠️ Tech Stack

* **Backend:** Python, Flask
* **AI / LLM Engine:** Ollama (e.g., Llama 3, Phi-3)
* **Vector Database:** ChromaDB
* **Relational Database:** Microsoft SQL Server
* **Data Processing:** Pandas, PyPDF/PDFPlumber
* **Frontend:** HTML5, CSS3, Bootstrap

## 📋 Prerequisites

Before running this application, ensure you have the following installed:
1. [Python 3.8+](https://www.python.org/downloads/)
2. [Ollama](https://ollama.com/) (with a local model pulled, e.g., `ollama run phi3`)
3. [Microsoft SQL Server](https://www.microsoft.com/en-us/sql-server/sql-server-downloads) (Express or Developer edition)

## 🚀 Installation & Setup

**1. Clone the repository**
```bash
git clone [https://github.com/UDAYABHAVANI/Medical-Document-Analysis-RAG-Health-app-.git](https://github.com/UDAYABHAVANI/Medical-Document-Analysis-RAG-Health-app-.git)
cd Medical-Document-Analysis-RAG-Health-app-