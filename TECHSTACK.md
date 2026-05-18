# 🔬 SafeScan - AI Ingredient Scanner

An AI-powered ingredient scanner application that analyzes product images to extract ingredients and assess safety based on different health profiles.

## 📋 Tech Stack

### **Frontend**
- **Streamlit** - Interactive web UI for product scanning and data visualization

### **Backend**
- **Python 3.11+** - Core backend runtime
- **FastAPI** - RESTful API framework
- **Uvicorn** - ASGI server

### **OCR & Image Processing**
- **PaddleOCR** - Optical Character Recognition for ingredient extraction
- **PIL (Pillow)** - Image enhancement and processing

### **Database**
- **SQLite** - Lightweight, file-based database
- **SQLAlchemy** - ORM for database operations
- **Pydantic** - Data validation and serialization

### **Visualization & Data**
- **Plotly** - Interactive charts and dashboards
- **Pandas** - Data manipulation and analysis

### **Utilities**
- **RapidFuzz** - Fuzzy string matching for ingredient matching

## 🚀 Getting Started

### Prerequisites
- Python 3.11 or higher

### Running the Application

**Start Backend API (Terminal 1):**
```bash
python -m uvicorn backend.app:app --host 0.0.0.0 --port 8000 --reload
```

**Start Streamlit Frontend (Terminal 2):**
```bash
streamlit run main_app.py
```

### Access the Application
- **Streamlit UI**: http://localhost:8501
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## 📁 Project Structure

```
Scanner/
├── backend/
│   ├── __init__.py
│   ├── app.py              # FastAPI application
│   ├── database.py         # SQLAlchemy setup
│   ├── models.py           # Database models
│   ├── schemas.py          # Pydantic schemas
│   └── scan_service.py     # OCR & analysis logic
├── main_app.py             # Streamlit main application
├── run.sh                  # Startup script
├── requirements.txt        # Python dependencies
├── pyproject.toml         # Project configuration
├── package.json           # Node.js config (minimal)
└── README.md              # This file
```

## 📊 Features

### 🏠 Home Page
- Project overview and information
- Tech stack details

### 📸 Scan Product
- Upload product images
- Automatic ingredient extraction using OCR
- Risk assessment based on extracted ingredients
- Profile-specific analysis (Children, Pregnant, Elderly, Allergen Sensitive)

### 📊 Dashboard
- View statistics and metrics
- Interactive charts and visualizations
- Risk score trends
- Grade distribution

### 📚 Database
- Browse ingredient database
- View ingredients by risk level
- Search and filter capabilities

### 📋 History
- Review past scans
- Export scan history as CSV
- Track scanning patterns

## 🧠 How It Works

1. **Image Upload**: User uploads a product image
2. **OCR Processing**: PaddleOCR extracts text from the image
3. **Ingredient Matching**: Extracted text is matched against the ingredient database using fuzzy matching
4. **Risk Assessment**: Matched ingredients are scored based on risk levels
5. **Grade Assignment**: Overall safety grade (A-F) is assigned
6. **Result Storage**: Results are saved to SQLite database
7. **Visualization**: Results are displayed with interactive Plotly charts

## 🗄️ Database Schema

### Ingredients Table
- `id`: Primary key
- `name`: Ingredient name
- `code`: E-number or ingredient code
- `category`: Ingredient category
- `risk_level`: low/medium/high
- `description`: Ingredient description
- `safety_notes`: Safety information
- `profile_flags`: Relevant for specific profiles

### Scan History Table
- `id`: Primary key
- `product_name`: Name of scanned product
- `raw_text`: Extracted text from image
- `grade`: Safety grade (A-F)
- `risk_score`: Numeric risk score (0-10)
- `profile`: Profile used for analysis
- `result_json`: JSON with detailed results
- `created_at`: Scan timestamp

### Ingredient Match Stats Table
- `id`: Primary key
- `ingredient_id`: Reference to ingredient
- `match_count`: Number of times matched

## 🔌 API Endpoints

### Health Check
- `GET /health` - Server status

### Scanning
- `POST /api/scan` - Analyze product image

### Ingredients
- `GET /api/ingredients` - Get all ingredients
- `GET /api/ingredients/{id}` - Get specific ingredient
- `POST /api/ingredients` - Create new ingredient

### History
- `GET /api/scan-history` - Get scan history
- `GET /api/statistics` - Get application statistics

## ⚙️ Configuration

### Environment Variables
```bash
DATABASE_URL=sqlite:///./ingredient_scanner.db  # Database path
PADDLE_OCR_LANG=en                              # OCR language
```

## 🧪 Development

### Running Tests
```bash
pytest tests/
```

### Code Formatting
```bash
black backend/ main_app.py
```

### Linting
```bash
flake8 backend/ main_app.py
```

## 📦 Building & Deployment

### Create Executable
```bash
pyinstaller --onefile main_app.py
```

### Docker Support
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["bash", "run.sh"]
```

## 📝 License

MIT License - See LICENSE file for details

## 👥 Contributors

- Ramya DR (RamyaDR2005)

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📞 Support

For issues or questions, please open an issue on GitHub.

---

**SafeScan v1.0** - *AI-Powered Ingredient Scanner*
