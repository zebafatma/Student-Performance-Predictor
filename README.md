# Student Performance Predictor

## Overview

Student Performance Predictor is a Machine Learning-based web application that predicts a student's academic performance using various input parameters such as study habits, attendance, previous scores, and other relevant factors. The project helps educators and students analyze performance trends and make informed decisions to improve academic outcomes.

---

## Features

* Predicts student performance using a trained Machine Learning model
* User-friendly React frontend
* FastAPI backend for fast prediction requests
* Interactive and responsive interface
* Data visualization using charts
* CSV dataset support
* REST API integration
* Report generation support

---

## Tech Stack

### Frontend

* React.js
* Chart.js
* React ChartJS 2
* HTML
* CSS
* JavaScript

### Backend

* FastAPI
* Python
* Scikit-learn
* Pandas
* Joblib
* Uvicorn

---

## Project Structure

```text
Student_Predictor/
│
├── frontend/
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── ...
│
├── backend/
│   ├── app.py
│   ├── model.joblib
│   ├── students.csv
│   ├── requirements.txt
│   └── predictions.db
│
└── README.md
```

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/Student-Performance-Predictor.git
cd Student_Predictor
```

---

## Backend Setup

Navigate to the backend folder:

```bash
cd backend
```

Create a virtual environment (recommended):

### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

### Install dependencies

```bash
pip install -r requirements.txt
```

Start the FastAPI server:

```bash
uvicorn app:app --reload
```

Backend runs at:

```text
http://127.0.0.1:8000
```

---

## Frontend Setup

Open a new terminal.

Navigate to the frontend folder:

```bash
cd frontend
```

Install dependencies:

```bash
npm install
```

Start the React application:

```bash
npm start
```

Frontend runs at:

```text
http://localhost:3000
```

---

## How It Works

1. User enters student information.
2. React sends the data to the FastAPI backend.
3. The trained Machine Learning model processes the input.
4. The predicted student performance is returned.
5. Results are displayed instantly with visual insights.

---

## Future Enhancements

* User authentication
* Model retraining from new datasets
* Multiple prediction algorithms
* Teacher dashboard
* Student history tracking
* Cloud deployment
* Performance analytics

---

## Requirements

### Backend

* Python 3.10+
* FastAPI
* Uvicorn
* Scikit-learn
* Pandas
* Joblib

### Frontend

* Node.js
* npm

---

## License

This project was developed for educational and learning purposes.
