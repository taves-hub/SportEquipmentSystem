# Sports Equipment System

## Bulk Upload Equipment (CSV)

### Overview
The system supports bulk uploading equipment inventory via CSV or PDF files. This feature allows administrators to quickly add or update multiple equipment items at once.

### File Format

#### CSV Format
Create a CSV file with the following columns:

```csv
name,category,category_code,quantity
Ball,Football,FTB01,50
Net,Football,FTB02,30
Racket,Tennis,TEN01,20
Shoes,Running,RUN01,15
Hoop,Basketball,BAS01,10
```

#### Column Descriptions

| Column | Description | Required | Example |
|--------|-------------|----------|---------|
| **name** | Equipment name | Yes | Ball, Net, Racket |
| **category** | Equipment category | No | Football, Tennis, Running |
| **category_code** | Unique category code (letters & numbers only) | Yes | FTB01, TEN01, RUN01 |
| **quantity** | Number of items to add | Yes | 50, 30, 20 |

### PDF Format
PDF files should contain a table with the same columns as the CSV format:
- `name`, `category`, `category_code`, `quantity`

The system will automatically extract the first table found in the PDF.

### Upload Instructions

1. **Navigate to Equipment Management**
   - Go to Admin Panel → Equipment page

2. **Prepare Your File**
   - Create a CSV file with equipment data
   - Or extract a table into a PDF document

3. **Upload the File**
   - Click "Choose File" and select your CSV or PDF
   - Click "Preview Upload"

4. **Review Preview**
   - Check the preview page for any issues
   - Rows with errors will be highlighted
   - Valid rows show whether they will create new items or update existing ones

5. **Confirm & Import**
   - Click "Confirm and Import" to commit changes to database

### Duplicate Handling

- **If equipment already exists** (same `category_code` AND `name`): The quantity will be **incremented** by the uploaded amount
- **If equipment is new**: A new record will be created

### Sample Template

Save this as `equipment_template.csv`:

```csv
name,category,category_code,quantity
Football,Football,FTB01,50
Volleyball,Football,FTB02,30
Tennis Racket,Tennis,TEN01,20
Running Shoes,Running,RUN01,15
Basketball Hoop,Basketball,BAS01,10
Badminton Racket,Badminton,BAD01,25
Shuttlecock,Badminton,BAD02,100
Hockey Stick,Hockey,HOC01,30
Hockey Ball,Hockey,HOC02,50
```

### Important Notes

- **Category Code** must be unique per equipment (letters and numbers only, max 10 characters)
- **Name** and **Category Code** are required fields
- **Quantity** must be a positive integer
- Column names are case-insensitive and auto-normalized
- Invalid rows will be skipped with warning messages
- The system supports UTF-8 encoded files

### Troubleshooting

| Issue | Solution |
|-------|----------|
| "No file uploaded" | Select a file before clicking Preview Upload |
| "Failed to read CSV file" | Ensure file is UTF-8 encoded and valid CSV format |
| "Unsupported file type" | Only CSV and PDF files are supported |
| Rows showing errors | Check for missing `name` or `category_code` values |
| PDF not extracting | Ensure the PDF contains a table with the expected columns |

### Example: Adding 100 Items at Once

```csv
name,category,category_code,quantity
Dumbbell 5kg,Weights,WGT01,100
Dumbbell 10kg,Weights,WGT02,80
Yoga Mat,Yoga,YOG01,50
Resistance Band,Yoga,YOG02,75
Jump Rope,Cardio,CAR01,120
Skipping Rope,Cardio,CAR02,100
```

Simply upload this file and it will add all items in one operation!
