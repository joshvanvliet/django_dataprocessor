# Data Processing Dashboard

Django-based web application used for processing and visualizing structured data entries from both JSON and XML, including grading of data quality.

## Features

- Data ingestion from flat XML and JSON sources
- Data quality scoring  
- Web dashboard with search bar and pagination
- Clipboard integration for data copying
- Responsive design for all screen sizes and devices

## Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/joshvanvliet/django_dataprocessor
   cd django_dataprocessor
   ```

2. **Set up virtual environment (optional)**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure database**
   ```bash
   python manage.py migrate
   ```

## Usage

### Key Commands

- **Clear database entries**
  ```bash
  python manage.py flush
  ```

- **Process example data files**
  ```bash
  python manage.py process_data
  ```

- **Start development server**
  ```bash
  python manage.py runserver
  ```

Access the dashboard at: [http://localhost:8000](http://localhost:8000)
