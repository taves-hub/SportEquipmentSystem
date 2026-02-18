# Sports Equipment Management System
## Storekeeper User Manual

---

## Table of Contents
1. [Getting Started](#getting-started)
2. [Login Instructions](#login-instructions)
3. [Registration Process](#registration-process)
4. [Dashboard Overview](#dashboard-overview)
5. [Main Features & How to Use](#main-features--how-to-use)
6. [Common Tasks](#common-tasks)
7. [Troubleshooting](#troubleshooting)

---

## Getting Started

The Sports Equipment Management System is a web-based platform designed to help storekeepers manage the distribution, issuance, and tracking of sports equipment across campus locations.

### System Requirements
- **Browser**: Chrome, Firefox, Safari, or Edge (latest version)
- **Internet Connection**: Stable internet connection required
- **Device**: Desktop, Laptop, or Tablet
- **Credentials**: Payroll number and password (provided by admin)

### Accessing the System
1. Open your web browser
2. Navigate to: `http://127.0.0.1:5000/` (or your institution's URL)
3. You will be redirected to the login page

---

## Login Instructions

### Step 1: Access Login Page
Navigate to the login page. You'll see:
- University of Nairobi logo
- Login form with two fields
- Option to register as a new storekeeper

### Step 2: Enter Your Credentials
1. **Username Field**: Enter your **6-digit payroll number**
   - Example: `123456`
   - This is your unique identifier in the system

2. **Password Field**: Enter your assigned password
   - Your initial password is provided by the admin
   - Passwords are case-sensitive
   - Click the eye icon (👁️) to show/hide password

### Step 3: Sign In
1. Click the **"Sign In"** button
2. Wait for the system to authenticate your credentials
3. You will be redirected to your dashboard

### Login Issues?
- **"Payroll number or username not found"**: Check that your payroll number is correct (6 digits)
- **"Invalid password"**: Verify your password is correct; passwords are case-sensitive
- **"Your account is pending approval"**: Your admin has not yet approved your registration. Check back later.

---

## Registration Process

### For New Storekeepers

If you don't have an account, follow these steps:

#### Step 1: Click "Register as Storekeeper"
On the login page, click the **"Register as Storekeeper"** link at the bottom.

#### Step 2: Fill in Registration Form

**Required Information:**

1. **Payroll Number** (Required)
   - Your 6-digit employee ID
   - Must be unique (cannot be used twice)
   - Example: `654321`

2. **Full Name** (Required)
   - Your complete name as it appears in official records
   - Example: `John Doe`

3. **Email Address** (Required)
   - Your institutional or personal email
   - Must be unique (cannot be duplicated across system)
   - Example: `john.doe@university.ac.ke`

4. **Select Campus** (Required)
   - Choose your assigned satellite campus from the dropdown
   - Contact admin if your campus is not listed

5. **Password** (Required)
   - Minimum 6 characters
   - Use a strong password with numbers, letters, and special characters if possible
   - Example: `SecurePass123`

6. **Confirm Password** (Required)
   - Re-enter your password to confirm
   - Passwords must match

#### Step 3: Submit Registration
1. Click the **"Register"** button
2. A success message will appear
3. Your account is now pending admin approval
4. You will receive notification once approved

**Note**: You cannot log in until your account is approved by the system administrator.

---

## Dashboard Overview

Once logged in, you'll see your **Storekeeper Dashboard** displaying:

### Dashboard Components

#### 1. **Top Navigation Bar**
- Your name and payroll number (top right)
- Quick access notifications bell icon
- Logout option

#### 2. **Main Statistics Cards**
- **Total Equipment**: Number of equipment items distributed to your campus
- **Active Items**: Equipment currently available for issuing
- **Total Issued**: Equipment currently issued to students/staff
- **Items Due**: Number of items that need to be returned
- **Damaged/Lost**: Items reported as damaged or lost during use

#### 3. **Low Stock Alerts** (if applicable)
- Lists equipment running low on available stock
- Shows current availability vs. total distributed quantity
- Helps you know when to request more stock

#### 4. **Overdue Items** (if applicable)
- Shows equipment that should have been returned
- Displays expected return dates
- Helps track accountability

---

## Main Features & How to Use

### 1. **Issue Equipment to Students**

#### Purpose
Issue sports equipment to students for use during practices, games, or training.

#### Steps:
1. Click **"Issue Equipment"** in the main menu
2. Select the equipment you want to issue
3. Enter:
   - **Student ID/Name**: Identify the student
   - **Quantity**: Number of items to issue
   - **Expected Return Date** (optional): When the equipment should be returned
   - **Item Condition**: Current condition of equipment (Good/Fair/Poor)
4. Click **"Issue Equipment"** button
5. A receipt/confirmation will be generated
6. Provide a copy to the student

**Best Practice**: Record the student's contact information and expected return date for follow-up.

---

### 2. **Issue Equipment to Staff**

#### Purpose
Issue equipment to staff members for departmental use.

#### Steps:
1. Click **"Issue Equipment"** in the main menu
2. Select **"Staff Member"** option if available
3. Enter:
   - **Staff Payroll Number**: Identify the staff member
   - **Full Name**: Staff member's name
   - **Quantity**: Number of items
   - **Expected Return Date**: When item should be returned
4. Complete the issuance and record details

---

### 3. **Receive Returned Equipment**

#### Purpose
Process equipment returns and check condition.

#### Steps:
1. Click **"Return Equipment"** in the main menu
2. Enter the **Student/Staff ID** who is returning the item
3. Review the equipment details:
   - Equipment name and serial number
   - Original condition
   - Quantity issued
4. Inspect the returned equipment and select **Condition**:
   - **Good**: No damage
   - **Fair**: Minor wear or damage
   - **Damaged**: Significant damage
   - **Lost**: Equipment missing
5. Add **Notes** if necessary (e.g., "Torn strap", "Missing wheel")
6. Click **"Process Return"**
7. Generate receipt for the student/staff

**Important**: Carefully inspect equipment before accepting returns. Report any damage to your supervisor.

---

### 4. **View Receipts**

#### Purpose
Search and view all issued equipment receipts.

#### Steps:
1. Click **"Receipts"** in the main menu
2. Use the **Search Box**:
   - Search by Student ID
   - Search by Student Name
   - Search by Staff Payroll Number
3. View receipt details:
   - Equipment issued
   - Quantity
   - Date of issue
   - Expected return date
   - Recipient name and contact
4. Print or download receipt if needed

---

### 5. **Clearance Report**

#### Purpose
Track clearance status for students/staff you've issued equipment to.

#### Steps:
1. Click **"Clearance Report"** in the main menu
2. View status breakdown:
   - **Cleared**: Student has returned all equipment in good condition
   - **Pending**: Awaiting equipment return
   - **Overdue**: Equipment not returned by expected date
3. Search specific student/staff using **Search Box**
4. Use filters to view by status
5. Generate PDF report if needed

---

### 6. **View Equipment Inventory**

#### Purpose
See all equipment distributed to your campus.

#### Steps:
1. Click **"My Equipment"** in the main menu
2. View equipment details:
   - Equipment name and type
   - Category code
   - Total quantity distributed
   - Currently available stock
   - Condition status
3. Click on equipment name for detailed view:
   - Item serial numbers
   - Issue history
   - Return history

---

### 7. **Equipment Report**

#### Purpose
Generate detailed reports about equipment distribution and status.

#### Steps:
1. Click **"Reports"** in the main menu
2. Choose report type:
   - **Equipment Report**: Summary of all distributed equipment
   - **Issued Equipment Report**: Current inventory status
   - **Return Report**: All returned items and conditions
3. Select **Date Range** if filtering by date
4. Click **"Generate Report"**
5. View or download as PDF

---

## Common Tasks

### Task 1: Issue Equipment to a Student

**Scenario**: A student needs a basketball for a practice session.

**Steps**:
1. Navigate to **"Issue Equipment"**
2. Select basketball from the dropdown
3. Enter student ID (e.g., "45678")
4. Quantity: 1
5. Expected return date: Today or next scheduled practice
6. Item condition: Good
7. Click "Issue Equipment"
8. Record the receipt number for your records

---

### Task 2: Check Equipment Status

**Scenario**: You need to know how much equipment is currently available.

**Steps**:
1. Go to **"My Equipment"**
2. Scroll through the list
3. Check "Available Stock" column
4. If low, contact admin for additional distribution

---

### Task 3: Process a Return with Damage

**Scenario**: A student returns a volleyball with a tear.

**Steps**:
1. Go to **"Return Equipment"**
2. Enter student ID
3. Select the volleyball from the list
4. Select condition: **"Damaged"**
5. In notes, write: "Tear in seam (left side)"
6. Click "Process Return"
7. Submit damage report to supervisor if amount is significant

---

### Task 4: Generate a Clearance Report

**Scenario**: You need to verify that all equipment issued to Biology Department is accounted for.

**Steps**:
1. Go to **"Clearance Report"**
2. View total items issued
3. Check which items are:
   - Cleared (returned good condition)
   - Pending (awaiting return)
   - Overdue (past return date)
4. Follow up with students whose items are overdue
5. Print report if needed

---

## Troubleshooting

### Problem: "I forgot my password"

**Solution**:
1. Click **"Forgot Password"** on login page (if available)
2. Or contact your system administrator
3. Admin will reset your password temporarily
4. You can change it after logging in

**To change password** (if available):
1. Log in to system
2. Click your name in top-right corner
3. Select "Settings" or "Change Password"
4. Enter current password
5. Enter new password twice
6. Click "Update"

---

### Problem: "Equipment not appearing in my dropdown"

**Possible Causes**:
1. Equipment not distributed to your campus
2. Equipment is inactive/removed
3. Filters applied to view

**Solution**:
1. Contact admin to distribute equipment to your campus
2. Check if equipment is marked as "Active"
3. Clear any active filters
4. Refresh the page (Ctrl+R or Cmd+R)

---

### Problem: "Cannot find a student receipt"

**Solution**:
1. Go to **"Receipts"**
2. Try searching by:
   - Exact student ID number
   - Partial student name
   - Date range
3. Use **"View All"** to see all receipts
4. Check if student ID is entered correctly

---

### Problem: "System is slow or timing out"

**Solution**:
1. Check your internet connection
2. Refresh the page (Ctrl+R)
3. Clear browser cache:
   - Chrome: Ctrl+Shift+Delete
   - Firefox: Ctrl+Shift+Delete
4. Try using a different browser
5. Contact your administrator if problem persists

---

### Problem: "I see 'Pending Approval' message"

**Explanation**: Your account registration was received but not yet approved by the administrator.

**Solution**:
1. Wait for admin approval (typically 1-2 business days)
2. Contact your administrator to accelerate approval
3. Try logging in again tomorrow
4. Check your email for approval notification

---

### Problem: "Equipment serial numbers not showing"

**Explanation**: This system tracks equipment by quantity, not individual serial numbers.

**Note**: Serial numbers are recorded when equipment enters the main system, but not for campus-level distributions.

---

### Problem: "Can't upload document attachment"

**Supported File Types**:
- PDF (.pdf)
- Word (.doc, .docx)
- Excel (.xls, .xlsx)
- Images (.jpg, .jpeg, .png)

**Solution**:
1. Check file format matches above
2. Ensure file size is under 10MB
3. Use PDF format for best compatibility
4. Contact admin if still having issues

---

## Quick Reference

### Menu Navigation

| Option | Purpose |
|--------|---------|
| Dashboard | View overview & stats |
| Issue Equipment | Issue to students/staff |
| Return Equipment | Process returns |
| Receipts | Search issued items |
| My Equipment | View available stock |
| Clearance Report | Track clearance status |
| Reports | Generate reports |
| Notifications | View system alerts |
| Settings | Change password |
| Logout | Exit system |

---

## Contact & Support

### For Technical Issues
- **Administrator Email**: admin@university.ac.ke
- **System Support**: IT Help Desk - Extension 1234
- **Emergency Contact**: +254 (emergency only)

### For Equipment Issues
- **Campus Supervisor**: [Your Campus Name]
- **Equipment Manager**: [Contact Name]

---

## Additional Notes

### Password Security
- Never share your password with anyone
- Change password regularly (every 30 days recommended)
- Use a unique password not used on other systems
- If you suspect password compromise, contact admin immediately

### Data Privacy
- All transactions are logged and auditable
- Treat student information as confidential
- Don't access or modify records of another storekeeper

### Best Practices
1. **Always issue receipts**: Every item issued should have documented receipt
2. **Inspect equipment**: Check condition before and after issue
3. **Record damages**: Report damaged items immediately
4. **Follow up returns**: Contact students about overdue items promptly
5. **Keep notes**: Use comments field to record important details
6. **Regular audits**: Periodically verify your equipment inventory

---

## Version Information
- **System Version**: 1.0
- **Last Updated**: February 13, 2026
- **For Questions**: Contact System Administrator

---

**Thank you for using the Sports Equipment Management System!**
