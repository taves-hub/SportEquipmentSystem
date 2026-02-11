#!/usr/bin/env python3
"""Generate comprehensive Admin Module Documentation PDF"""

from fpdf import FPDF
from datetime import datetime

class AdminDocPDF(FPDF):
    def header(self):
        self.set_font("Arial", "B", 16)
        self.cell(0, 10, "Sports Equipment Management System", new_x="LMARGIN", new_y="NEXT", align="C")
        self.set_font("Arial", "I", 12)
        self.cell(0, 10, "Admin Panel - Complete Module Documentation", new_x="LMARGIN", new_y="NEXT", align="C")
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")

    def chapter_title(self, title):
        self.set_fill_color(200, 220, 255)
        self.set_font("Arial", "B", 14)
        self.cell(0, 10, title, new_x="LMARGIN", new_y="NEXT", fill=True)
        self.ln(3)

    def chapter_heading(self, heading):
        self.set_font("Arial", "B", 11)
        self.cell(0, 8, heading, new_x="LMARGIN", new_y="NEXT")

    def normal_text(self, text):
        self.set_font("Arial", "", 10)
        self.multi_cell(0, 5, text)

    def table_header(self, headers):
        self.set_fill_color(100, 150, 200)
        self.set_text_color(255, 255, 255)
        self.set_font("Arial", "B", 9)
        for h in headers:
            self.cell(0, 7, h, border=1, align="L", new_x="LMARGIN", new_y="NEXT")
        self.set_text_color(0, 0, 0)

    def add_module_info(self, module_name, description, route, methods, features):
        self.chapter_heading(module_name)
        self.set_font("Arial", "", 9)
        self.multi_cell(0, 4, f"Route: {route}\nMethods: {methods}")
        self.ln(2)
        self.multi_cell(0, 4, f"Description: {description}")
        self.ln(2)
        self.set_font("Arial", "B", 9)
        self.multi_cell(0, 4, "Key Features:")
        self.set_font("Arial", "", 8)
        for feature in features:
            self.multi_cell(185, 3, f"- {feature}")
        self.ln(1)


def generate_admin_pdf():
    pdf = AdminDocPDF()
    pdf.add_page()

    # INTRODUCTION
    pdf.chapter_title("ADMIN PANEL OVERVIEW")
    pdf.normal_text(
        "The Admin Panel serves as the central control hub for the entire Sports Equipment Management System. Admins have comprehensive access to:\n\n"
        "1. Equipment Inventory Management\n"
        "2. Equipment Distribution & Logistics\n"
        "3. Damage/Loss Clearance Review & Approval\n"
        "4. User Account Management\n"
        "5. Reporting & Analytics\n"
        "6. Campus & Facility Management\n"
        "7. Equipment Issuance & Returns"
    )
    pdf.ln(5)

    # DASHBOARD MODULE
    pdf.chapter_title("MODULE 1: ADMIN DASHBOARD")
    pdf.add_module_info(
        "Dashboard Overview",
        "Real-time system overview with key metrics and alerts. Provides snapshot of critical system status.",
        "GET /admin/dashboard",
        "GET",
        [
            "Total equipment count in inventory",
            "Total cleared recipients (Students + Staff)",
            "Returned equipment breakdown (Good, Damaged, Lost)",
            "Due items alert - equipment not yet returned past expected return date",
            "Escalated damage/loss items pending admin review",
            "Distribution metrics (campus distributions, quantities)",
            "Unread notifications counter",
            "Total recipients count (Students + Staff)"
        ]
    )
    pdf.ln(3)

    # EQUIPMENT MANAGEMENT MODULE
    pdf.chapter_title("MODULE 2: EQUIPMENT INVENTORY MANAGEMENT")
    
    pdf.add_module_info(
        "2.1 View & Manage Equipment",
        "Browse and manage all equipment in the system. Add, edit, delete, and toggle equipment status.",
        "GET/POST /admin/equipment",
        "GET, POST",
        [
            "List all equipment organized by category and category code",
            "Add new equipment with name, category, quantity",
            "Update existing equipment quantities",
            "Toggle equipment active/inactive status",
            "Delete equipment items (with proper checks)",
            "Category-based organization and filtering"
        ]
    )
    
    pdf.add_module_info(
        "2.2 Equipment Upload & Import",
        "Bulk import equipment from CSV file. Supports preview and confirmation workflow.",
        "POST /admin/equipment/upload",
        "POST",
        [
            "CSV file upload with validation",
            "Preview changes before confirming",
            "Support for new items and quantity updates",
            "Error handling for malformed data",
            "Session-based preview storage",
            "Batch processing with error reporting"
        ]
    )

    pdf.add_module_info(
        "2.3 Equipment Export",
        "Export all inventory as CSV for external reporting or backup.",
        "GET /admin/equipment/export-csv",
        "GET",
        [
            "Download equipment list as CSV",
            "Grouped by category code",
            "Includes quantity and date received",
            "Formatted for easy import into external systems"
        ]
    )

    pdf.add_module_info(
        "2.4 Equipment Edit",
        "Modify individual equipment details after creation.",
        "GET/POST /admin/equipment/<equipment_id>/edit",
        "GET, POST",
        [
            "Edit equipment name, category, quantity",
            "Audit trail for modifications",
            "Validation of input data",
            "Confirmation before saving changes"
        ]
    )

    pdf.add_module_info(
        "2.5 Equipment Toggle Status",
        "Enable or disable equipment from being issued without deletion.",
        "POST /admin/equipment/<equipment_id>/toggle",
        "POST",
        [
            "Mark equipment as inactive (no longer issued)",
            "Mark equipment as active (available for issuance)",
            "Preserves historical data",
            "AJAX-based for quick status changes"
        ]
    )

    pdf.add_module_info(
        "2.6 Equipment Delete",
        "Permanently remove equipment from system (use carefully).",
        "POST /admin/equipment/<equipment_id>/delete",
        "POST",
        [
            "Permanent removal from inventory",
            "Safety checks before deletion",
            "Confirmation required",
            "Cleanup of related records"
        ]
    )
    pdf.ln(3)

    # DISTRIBUTION MODULE
    pdf.chapter_title("MODULE 3: CAMPUS DISTRIBUTION & LOGISTICS")
    
    pdf.add_module_info(
        "3.1 Distribute to Campus",
        "Allocate equipment from central inventory to satellite campuses.",
        "GET/POST /admin/distribute-to-campus",
        "GET, POST",
        [
            "Select equipment and quantity",
            "Choose destination campus",
            "Record distribution date and details",
            "Generate distribution document",
            "Track distributed quantities per campus",
            "Campus-specific inventory allocation"
        ]
    )

    pdf.add_module_info(
        "3.2 Manage Campuses",
        "CRUD operations for satellite campus locations.",
        "GET/POST /admin/manage-campuses",
        "GET, POST",
        [
            "Add new satellite campuses",
            "Edit campus details (name, location, contact)",
            "Activate/deactivate campuses",
            "View campus storekeeper assignments",
            "Manage campus contact information"
        ]
    )

    pdf.add_module_info(
        "3.3 View Distributions",
        "List all historical and current distributions to campuses.",
        "GET /admin/distributions",
        "GET",
        [
            "View all campus distributions",
            "Distribution date and quantity tracking",
            "Campus assignment details",
            "Storekeeper responsible for each distribution",
            "Document download capability"
        ]
    )

    pdf.add_module_info(
        "3.4 Download Distribution Document",
        "Export distribution document as PDF for record keeping.",
        "GET /admin/download-distribution-document/<distribution_id>",
        "GET",
        [
            "Generate PDF distribution document",
            "Include equipment list and quantities",
            "Campus and storekeeper details",
            "Date and authorization information"
        ]
    )
    pdf.ln(3)

    # EQUIPMENT ISSUANCE MODULE
    pdf.chapter_title("MODULE 4: EQUIPMENT ISSUANCE & RETURNS")
    
    pdf.add_module_info(
        "4.1 Issue Equipment",
        "Directly issue equipment from admin level to students/staff. Can bypass campus allocation if needed.",
        "GET/POST /admin/issue",
        "GET, POST",
        [
            "Issue equipment directly from central inventory",
            "Search and select recipient (student/staff)",
            "Choose equipment and quantity",
            "Set expected return date",
            "Record issuing admin details",
            "Generate issue receipt immediately",
            "Track serial numbers (if applicable)",
            "Support for both individual and bulk issuances"
        ]
    )

    pdf.add_module_info(
        "4.2 Process Returns",
        "Record equipment returns and document condition (Good, Damaged, Lost).",
        "GET/POST /admin/return/<issue_id>",
        "GET, POST",
        [
            "Select returned items from issue list",
            "Record condition of each item (Good/Damaged/Lost)",
            "Support for partial returns",
            "Add notes about damage or loss",
            "Update equipment status to Returned",
            "Record return date",
            "Trigger damage clearance flow if damaged/lost"
        ]
    )

    pdf.add_module_info(
        "4.3 View Issued Equipment",
        "List all equipment currently issued (status = 'Issued').",
        "GET /admin/issued-equipment",
        "GET",
        [
            "Show all outstanding issued items",
            "Recipient details and contact info",
            "Equipment name and quantity",
            "Issue date and expected return date",
            "Status at a glance",
            "Filter and search capabilities"
        ]
    )

    pdf.add_module_info(
        "4.4 View Issue Receipt",
        "Display formatted receipt for specific equipment issuance.",
        "GET /admin/issue-receipt/<issue_id> or /admin/issue-receipt/recipient/<recipient_id>",
        "GET",
        [
            "Print-friendly receipt format",
            "Equipment details and quantities",
            "Recipient information",
            "Issuing authority and date",
            "Serial numbers (if tracked)",
            "Expected return date"
        ]
    )

    pdf.add_module_info(
        "4.5 Recipient Autocomplete API",
        "AJAX endpoint for searching and autocompleting recipient names.",
        "GET /admin/api/recipient-autocomplete",
        "GET",
        [
            "Search student and staff names",
            "Real-time autocomplete suggestions",
            "Return recipient ID for selected person",
            "Filter by recipient type if needed"
        ]
    )
    pdf.ln(3)

    # DAMAGE/LOSS CLEARANCE MODULE
    pdf.chapter_title("MODULE 5: DAMAGE/LOSS CLEARANCE REVIEW")
    
    pdf.add_module_info(
        "5.1 Clearance Report",
        "View clearance status for all recipients (students/staff).",
        "GET /admin/clearance-report",
        "GET",
        [
            "List all recipients with clearance status",
            "Filter by recipient ID or name",
            "Clearance breakdown: Cleared/Pending/Overdue",
            "Associated issued items for each recipient",
            "Status indicators and notes",
            "Export to PDF or print capability"
        ]
    )

    pdf.add_module_info(
        "5.2 Manage Student Clearance",
        "Review and manage damage/loss clearance for specific student.",
        "GET/POST /admin/clearance/<student_id>/manage",
        "GET, POST",
        [
            "Review all damage/loss items for student",
            "View escalated items from storekeeper",
            "Approve clearance (mark as Cleared/Waived)",
            "Reject items for storekeeper re-review (Needs Review)",
            "Add admin notes and comments",
            "Track admin decision history",
            "Determine final clearance status"
        ]
    )

    pdf.add_module_info(
        "5.3 Manage Staff Clearance",
        "Same clearance review workflow for staff members.",
        "GET/POST /admin/clearance/staff/<staff_payroll>/manage",
        "GET, POST",
        [
            "Review damage/loss items for staff",
            "Approve or reject clearance",
            "Add admin notes",
            "Track staff clearance status",
            "Manage escalated items from storekeeper"
        ]
    )

    pdf.add_module_info(
        "5.4 View Escalated Items",
        "Review equipment escalated by storekeeper for admin decision.",
        "GET /admin/escalated-damage",
        "GET",
        [
            "List all escalated damage/loss items",
            "View reason for escalation",
            "Storekeeper notes and assessment",
            "Equipment details and condition",
            "Recipient information",
            "Quick links to manage clearance"
        ]
    )

    pdf.add_module_info(
        "5.5 Process Escalated Item",
        "Make admin decision on escalated damage/loss item.",
        "POST /admin/escalated-damage/<issue_id>",
        "POST",
        [
            "Approve escalation (mark as Cleared/Waived)",
            "Reject and send back to storekeeper",
            "Add admin notes for decision",
            "Update damage clearance status",
            "Notify relevant parties"
        ]
    )

    pdf.add_module_info(
        "5.6 Rollback Clearance",
        "Return cleared items back to Needs Review for re-evaluation.",
        "GET/POST /admin/clearance/<recipient_id>/rollback",
        "GET, POST",
        [
            "View previously cleared items",
            "Select items to rollback to Needs Review",
            "Return items to storekeeper for re-review",
            "Add rollback reason/notes",
            "Reset status to 'Needs Review'",
            "Notify storekeeper of changes",
            "Audit trail of rollback actions"
        ]
    )

    pdf.add_module_info(
        "5.7 Clearance Items List",
        "Detailed view of all items requiring clearance for a recipient.",
        "GET/POST /admin/clearance/<recipient_id>/items",
        "GET, POST",
        [
            "List damaged/lost items for recipient",
            "Filter by clearance status",
            "Status values: Pending, Needs Review, Escalated, Cleared, Waived, etc.",
            "Make decisions on multiple items",
            "Bulk actions for clearance",
            "Detailed item information and notes"
        ]
    )
    pdf.ln(3)

    # REPORTING MODULE
    pdf.chapter_title("MODULE 6: REPORTING & ANALYTICS")
    
    pdf.add_module_info(
        "6.1 Reports Dashboard",
        "Central hub for all system reports and data exports.",
        "GET /admin/reports",
        "GET",
        [
            "Access to various report types",
            "Links to detailed reports",
            "Report generation options",
            "Export capability overview"
        ]
    )

    pdf.add_module_info(
        "6.2 Issued Equipment Report",
        "Detailed report of all issued equipment with recipients and dates.",
        "GET /admin/issued_report",
        "GET",
        [
            "List all issued equipment with details",
            "Recipient name and ID",
            "Issue and expected return dates",
            "Equipment quantity and conditions",
            "Filter by date range or recipient",
            "Export to CSV or print",
            "Status indicators"
        ]
    )

    pdf.add_module_info(
        "6.3 Equipment Report",
        "Inventory status report with distribution details.",
        "GET /admin/equipment-report",
        "GET",
        [
            "Total equipment in system",
            "Active vs inactive count",
            "Equipment distributed per campus",
            "Outstanding issued quantities",
            "Low stock indicators",
            "Category breakdown"
        ]
    )

    pdf.add_module_info(
        "6.4 Clearance Due Details",
        "Detailed list of recipients with overdue clearance.",
        "GET /admin/clearance-due-details/<recipient_id>",
        "GET",
        [
            "View why clearance is overdue",
            "List pending damage/loss items",
            "Outstanding issues requiring attention",
            "Contact information for follow-up"
        ]
    )

    pdf.add_module_info(
        "6.5 Analytics APIs",
        "Real-time data endpoints for dashboard visualizations.",
        "GET /admin/api/inventory_top, /api/return_conditions, /api/issues_timeseries",
        "GET",
        [
            "Top 5 most issued equipment",
            "Return condition breakdown",
            "Issuance trends over time",
            "JSON format for chart integration"
        ]
    )

    pdf.add_module_info(
        "6.6 Print & Export Reports",
        "Generate printable and exportable reports.",
        "GET /admin/clearance-report/print, /clearance-report/export",
        "GET",
        [
            "Print-friendly clearance report",
            "Export clearance data to CSV",
            "Formatted for external use",
            "Batch reporting capability"
        ]
    )
    pdf.ln(3)

    # USER MANAGEMENT MODULE
    pdf.chapter_title("MODULE 7: USER ACCOUNT MANAGEMENT")
    
    pdf.add_module_info(
        "7.1 User Management Dashboard",
        "Approve, reject, and manage storekeeper accounts.",
        "GET /admin/user-management",
        "GET",
        [
            "View pending storekeeper registrations",
            "Approve storekeeper accounts",
            "Reject storekeeper accounts",
            "Deactivate existing storekeepers",
            "View all active storekeepers",
            "Campus assignment tracking",
            "Status and activation date"
        ]
    )

    pdf.add_module_info(
        "7.2 Approve User",
        "Approve pending storekeeper registration.",
        "POST /admin/user-management/approve/<user_id>",
        "POST",
        [
            "Set status to active",
            "Send approval notification",
            "Enable login access",
            "Assign to campus"
        ]
    )

    pdf.add_module_info(
        "7.3 Reject User",
        "Reject storekeeper registration application.",
        "POST /admin/user-management/reject/<user_id>",
        "POST",
        [
            "Set status to rejected",
            "Send rejection notification",
            "Prevent account access",
            "Optional feedback to applicant"
        ]
    )

    pdf.add_module_info(
        "7.4 Deactivate User",
        "Deactivate active storekeeper account.",
        "POST /admin/user-management/deactivate/<user_id>",
        "POST",
        [
            "Set status to inactive",
            "Disable login access",
            "Preserve historical data",
            "Prevent future issuances"
        ]
    )
    pdf.ln(3)

    # PROFILE & SETTINGS
    pdf.chapter_title("MODULE 8: PROFILE & ACCOUNT SETTINGS")
    
    pdf.add_module_info(
        "8.1 Update Profile",
        "Update admin profile information.",
        "POST /admin/profile",
        "POST",
        [
            "Update full name and email",
            "Contact information",
            "Profile customization"
        ]
    )

    pdf.add_module_info(
        "8.2 Change Password",
        "Update admin account password.",
        "POST /admin/change-password",
        "POST",
        [
            "Secure password change",
            "Current password verification",
            "New password validation",
            "Password strength requirements"
        ]
    )
    pdf.ln(5)

    # FLOW DIAGRAM
    pdf.chapter_title("ADMIN WORKFLOW DIAGRAM")
    pdf.normal_text(
        "EQUIPMENT MANAGEMENT FLOW:\n"
        "Equipment Upload/Add -> Inventory -> Distribute to Campus -> Storekeeper Issues\n"
        "                                                    |\n"
        "                                              Equipment Return\n"
        "                                                    |\n"
        "                              Damage/Loss Detected? -> Storekeeper Review\n"
        "                                    |                      |\n"
        "                         YES -> Admin Review -> Approve/Reject\n"
        "                                    |                      |\n"
        "                      Reject -> Rollback -> Storekeeper Re-review\n"
        "                                    |                      |\n"
        "                         Approve -> Clearance -> Complete\n"
        "\n\n"
        "USER MANAGEMENT FLOW:\n"
        "Storekeeper Registration -> Pending -> Admin Review -> Approve/Reject\n"
        "                                              |              |\n"
        "                                        Approved      Rejected (End)\n"
        "                                              |\n"
        "                                        Active Account\n"
        "                                              |\n"
        "                            (Can be deactivated anytime)\n"
        "\n\n"
        "REPORTING & ANALYTICS FLOW:\n"
        "System Data -> Dashboard Metrics -> Reports -> Export/Print\n"
        "           -> Analytics APIs -> Charts & Visualizations\n"
    )
    pdf.ln(3)

    # MODULE RELATIONSHIPS
    pdf.chapter_title("MODULE RELATIONSHIPS & DATA FLOW")
    pdf.normal_text(
        "Equipment Inventory Management\n"
        "  |\n"
        "  +-> Distribution & Logistics\n"
        "  |      |\n"
        "  |      +-> Campus & Storekeeper Assignment\n"
        "  |\n"
        "  +-> Equipment Issuance\n"
        "       |\n"
        "       +-> Return Processing\n"
        "            |\n"
        "            +-> Damage/Loss Assessment\n"
        "                 |\n"
        "                 +-> Clearance Review (Admin)\n"
        "                      |\n"
        "                      +-> Clearance Status Determination\n"
        "\n"
        "User Management\n"
        "  |\n"
        "  +-> Storekeeper Approval\n"
        "  |      |\n"
        "  |      +-> Campus Assignment\n"
        "  |\n"
        "  +-> Account Deactivation\n"
        "\n"
        "Reporting & Analytics\n"
        "  |\n"
        "  +-> Equipment Reports\n"
        "  +-> Issuance Reports\n"
        "  +-> Clearance Reports\n"
        "  +-> Analytics Dashboards\n"
    )
    pdf.ln(5)

    # KEY METRICS & STATUS VALUES
    pdf.chapter_title("KEY METRICS & STATUS VALUES")
    pdf.normal_text(
        "EQUIPMENT STATUS VALUES:\n"
        "- Issued: Equipment given to recipient, awaiting return\n"
        "- Returned: Equipment returned in good condition\n"
        "- Partial Return: Some items returned, others pending\n"
        "\n"
        "CLEARANCE STATUS VALUES:\n"
        "- Pending: Item returned but not yet reviewed by storekeeper\n"
        "- Needs Review: Rejected by admin, requires storekeeper re-evaluation\n"
        "- Escalated: Storekeeper unable to resolve, sent to admin\n"
        "- Repaired: Item damaged but successfully repaired\n"
        "- Replaced: Item lost/damaged, replacement issued\n"
        "- Cleared: Admin approved clearance for item\n"
        "- Waived: Admin waived clearance requirement\n"
        "\n"
        "RECIPIENT CLEARANCE STATUS:\n"
        "- Cleared: All items for recipient have clearance status\n"
        "- Pending: Awaiting clearance on one or more items\n"
        "- Overdue: Clearance process delayed beyond expected timeline\n"
    )
    pdf.ln(3)

    # ADMIN CAPABILITIES SUMMARY
    pdf.chapter_title("ADMIN CAPABILITIES SUMMARY")
    pdf.normal_text(
        "1. FULL SYSTEM CONTROL: Access to all modules and data\n"
        "\n"
        "2. INVENTORY MANAGEMENT: Complete control over equipment lifecycle\n"
        "\n"
        "3. DISTRIBUTION: Allocate equipment to campuses and manage logistics\n"
        "\n"
        "4. ISSUANCE & RETURNS: Direct issue and return processing\n"
        "\n"
        "5. CLEARANCE AUTHORITY: Final decision maker on damage/loss items\n"
        "\n"
        "6. USER MANAGEMENT: Control over storekeeper account lifecycle\n"
        "\n"
        "7. REPORTING: Comprehensive system analytics and reporting\n"
        "\n"
        "8. ROLLBACK CAPABILITY: Ability to return cleared items for re-review\n"
        "\n"
        "9. REAL-TIME MONITORING: Dashboard with live system metrics\n"
        "\n"
        "10. AUDIT TRAIL: Complete history of all admin actions\n"
    )

    # Save PDF
    output_path = "Sports_Equipment_Admin_Panel_Documentation.pdf"
    pdf.output(output_path)
    print(f"[OK] PDF generated successfully: {output_path}")


if __name__ == "__main__":
    generate_admin_pdf()
