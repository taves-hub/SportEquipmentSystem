#!/usr/bin/env python3
"""Generate comprehensive Storekeeper Module Documentation PDF"""

from fpdf import FPDF
from datetime import datetime

class StorekeeperDocPDF(FPDF):
    def header(self):
        self.set_font("Arial", "B", 16)
        self.cell(0, 10, "Sports Equipment Management System", new_x="LMARGIN", new_y="NEXT", align="C")
        self.set_font("Arial", "I", 12)
        self.cell(0, 10, "Storekeeper Panel - Complete Module Documentation", new_x="LMARGIN", new_y="NEXT", align="C")
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


def generate_storekeeper_pdf():
    pdf = StorekeeperDocPDF()
    pdf.add_page()

    # INTRODUCTION
    pdf.chapter_title("STOREKEEPER PANEL OVERVIEW")
    pdf.normal_text(
        "The Storekeeper Panel is designed for campus-level equipment management and operations. Storekeepers are responsible for:\n\n"
        "1. Equipment Issuance to Students/Staff\n"
        "2. Equipment Return Processing & Condition Assessment\n"
        "3. Initial Damage/Loss Review & Assessment\n"
        "4. Equipment Escalation to Admin\n"
        "5. Campus Inventory Management\n"
        "6. Receipt & Documentation Generation\n"
        "7. Clearance Status Tracking\n"
        "\n"
        "Key Concept: Storekeepers handle day-to-day campus operations while admins handle final clearance approval."
    )
    pdf.ln(5)

    # DASHBOARD MODULE
    pdf.chapter_title("MODULE 1: STOREKEEPER DASHBOARD")
    pdf.add_module_info(
        "Dashboard Overview",
        "Campus-specific equipment and operations overview. Displays metrics for equipment allocated to this storekeeper's campus.",
        "GET /storekeeper/dashboard",
        "GET",
        [
            "Total equipment distributed to campus",
            "Total active equipment count",
            "Outstanding issued items count",
            "Damaged items count (pending clearance)",
            "Lost items count (pending clearance)",
            "Low stock alerts (5 items or fewer available)",
            "Due items - equipment not yet returned",
            "Unread notifications counter",
            "Campus name and assignment"
        ]
    )
    pdf.ln(3)

    # EQUIPMENT MODULE
    pdf.chapter_title("MODULE 2: CAMPUS EQUIPMENT MANAGEMENT")
    
    pdf.add_module_info(
        "2.1 View Campus Equipment",
        "Browse equipment allocated to this storekeeper's campus.",
        "GET /storekeeper/equipment",
        "GET",
        [
            "List all equipment distributed to campus",
            "View available quantities (distributed minus issued)",
            "Equipment status (active/inactive)",
            "Category and category code organization",
            "Low stock indicators",
            "Quick access to issue equipment"
        ]
    )

    pdf.add_module_info(
        "2.2 View Issued Equipment",
        "Track all equipment currently issued by this storekeeper.",
        "GET /storekeeper/issued-equipment",
        "GET",
        [
            "List outstanding issued items",
            "Recipient details (student/staff name and ID)",
            "Issue date and expected return date",
            "Equipment quantity and details",
            "Current status at a glance",
            "Filter and search capabilities"
        ]
    )
    pdf.ln(3)

    # ISSUANCE MODULE
    pdf.chapter_title("MODULE 3: EQUIPMENT ISSUANCE")
    
    pdf.add_module_info(
        "3.1 Issue Equipment",
        "Issue equipment from campus inventory to students/staff.",
        "GET/POST /storekeeper/issue",
        "GET, POST",
        [
            "Search and select recipient (student/staff)",
            "Auto-complete for recipient names",
            "Choose equipment from available campus inventory",
            "Specify quantity to issue",
            "Set expected return date",
            "Record equipment condition (assumed Good)",
            "Serial number tracking (if applicable)",
            "Generate issue receipt immediately",
            "Track issued_by storekeeper (via payroll number)",
            "Create IssuedEquipment record with date_issued"
        ]
    )

    pdf.add_module_info(
        "3.2 Recipient Auto-Complete API",
        "AJAX endpoint for searching recipients during issuance.",
        "GET /storekeeper/api/recipient-autocomplete",
        "GET",
        [
            "Real-time search of student and staff names",
            "Return matching recipients with IDs",
            "Filter autocomplete results",
            "Quick selection during issuance process"
        ]
    )

    pdf.add_module_info(
        "3.3 View Issue Receipt",
        "Display formatted receipt for issued equipment.",
        "GET /storekeeper/issue-receipt/<issue_id> or /storekeeper/issue-receipt/recipient/<recipient_id>",
        "GET",
        [
            "Print-friendly receipt format",
            "University logo and header",
            "Equipment list with quantities",
            "Recipient name and ID",
            "Issue date and expected return date",
            "Storekeeper/issuer information",
            "Receipt number",
            "Serial numbers (if tracked)"
        ]
    )
    pdf.ln(3)

    # RETURN PROCESSING MODULE
    pdf.chapter_title("MODULE 4: EQUIPMENT RETURN PROCESSING")
    
    pdf.add_module_info(
        "4.1 Return Equipment (Bulk)",
        "Process returns and assess condition for multiple items at once.",
        "GET/POST /storekeeper/return-equipment",
        "GET, POST",
        [
            "Search for items to return (by recipient or date)",
            "List outstanding issued items for review",
            "Select items to return",
            "Record return condition for each item (Good/Damaged/Lost)",
            "Support for partial returns",
            "Add notes about damage or loss",
            "Record return date automatically",
            "Store conditions in return_conditions JSON",
            "Update status to Returned or Partial Return"
        ]
    )

    pdf.add_module_info(
        "4.2 Return Individual Item",
        "Process return and condition assessment for a single issue.",
        "GET/POST /storekeeper/return/<issue_id>",
        "GET, POST",
        [
            "View specific issued item details",
            "Record return condition (Good/Damaged/Lost)",
            "Add damage/loss notes and description",
            "Update return date",
            "Mark as Returned or Partial Return",
            "Single item focus for detailed review"
        ]
    )
    pdf.ln(3)

    # DAMAGE/LOSS CLEARANCE MODULE
    pdf.chapter_title("MODULE 5: DAMAGE/LOSS CLEARANCE REVIEW")
    
    pdf.add_module_info(
        "5.1 Damage Clearance Dashboard",
        "View all damage/loss items returned to this campus awaiting review.",
        "GET /storekeeper/damage-clearance",
        "GET",
        [
            "List damage/lost items from campus returns",
            "Filter by status: Pending, Needs Review, Escalated, Cleared",
            "Needs Review status shown in yellow (high priority)",
            "Escalated items hidden (already with admin)",
            "Cleared items hidden (already resolved)",
            "Sort items by status and date",
            "Quick links to manage each item",
            "Recipient and equipment information",
            "Return condition details"
        ]
    )

    pdf.add_module_info(
        "5.2 Manage Damage Item",
        "Assess and make initial decision on damaged/lost equipment.",
        "POST /storekeeper/damage-clearance/<issue_id>",
        "POST",
        [
            "View detailed item information",
            "Two options available:",
            "  A) CLEAR: Item repaired or replaced",
            "     - Set status to Repaired or Replaced",
            "     - Record notes about repair/replacement",
            "     - Item leaves storekeeper view",
            "     - May trigger recipient clearance",
            "  B) ESCALATE: Send to admin for decision",
            "     - Set status to Escalated",
            "     - Include storekeeper assessment notes",
            "     - Item moves to admin escalated queue",
            "     - Notification sent to admin",
            "  - Track decision history",
            "  - Update damage_clearance_status field"
        ]
    )
    pdf.ln(3)

    # CLEARANCE REPORTING MODULE
    pdf.chapter_title("MODULE 6: CLEARANCE REPORTING")
    
    pdf.add_module_info(
        "6.1 Clearance Report",
        "View clearance status for recipients issued equipment by this storekeeper.",
        "GET /storekeeper/clearance-report",
        "GET",
        [
            "List recipients with clearance status",
            "Filter by recipient ID or name",
            "Clearance breakdown: Cleared/Pending/Overdue",
            "Display only items issued by this storekeeper",
            "Show associated issued items",
            "Status indicators (color-coded)",
            "Contact information for follow-up",
            "Issued by storekeeper and campus details"
        ]
    )
    pdf.ln(3)

    # RECEIPTS MODULE
    pdf.chapter_title("MODULE 7: RECEIPTS & DOCUMENTATION")
    
    pdf.add_module_info(
        "7.1 View Receipts",
        "List all receipts (grouped issuances to same recipient on same day).",
        "GET /storekeeper/receipts",
        "GET",
        [
            "Search receipts by recipient ID or name",
            "View grouped issuances (same recipient + same date combined)",
            "Display total equipment count per receipt",
            "Issue date and recipient details",
            "Quick links to view individual receipts",
            "Sorted by issue date (newest first)",
            "Filter by date range if needed"
        ]
    )

    pdf.add_module_info(
        "7.2 View Receipt Details",
        "Display grouped equipment from single receipt date.",
        "GET /storekeeper/issue-receipt/recipient/<recipient_id>?date=YYYY-MM-DD",
        "GET",
        [
            "Recipient name and ID",
            "Receipt date",
            "Combined equipment list for that date",
            "Equipment quantities and details",
            "Total items in receipt",
            "Print-friendly format",
            "University logo and branding"
        ]
    )

    pdf.add_module_info(
        "7.3 Download Distribution Document",
        "Export distribution document related to campus allocation.",
        "GET /storekeeper/download-distribution-document/<distribution_id>",
        "GET",
        [
            "PDF export of distribution details",
            "Campus allocation information",
            "Equipment list and quantities",
            "Storekeeper assignment",
            "Distribution date and authorization"
        ]
    )
    pdf.ln(3)

    # PROFILE & SETTINGS
    pdf.chapter_title("MODULE 8: PROFILE & ACCOUNT SETTINGS")
    
    pdf.add_module_info(
        "8.1 Update Profile",
        "Update storekeeper personal information.",
        "POST /storekeeper/profile",
        "POST",
        [
            "Update full name and email",
            "Contact information",
            "Profile customization",
            "Verification of current information"
        ]
    )

    pdf.add_module_info(
        "8.2 Change Password",
        "Update storekeeper account password.",
        "POST /storekeeper/change-password",
        "POST",
        [
            "Secure password change",
            "Current password verification",
            "New password validation",
            "Password strength requirements",
            "Account security enhancement"
        ]
    )
    pdf.ln(3)

    # NOTIFICATIONS
    pdf.chapter_title("MODULE 9: NOTIFICATIONS & ALERTS")
    
    pdf.add_module_info(
        "9.1 Notification Bell",
        "Real-time notification system for critical alerts.",
        "GET /storekeeper/api/notifications",
        "GET",
        [
            "Unread notifications counter",
            "Latest 10 unread notifications",
            "Auto-refresh every 5 seconds",
            "Notification messages and timestamps",
            "Quick navigation to relevant page"
        ]
    )

    pdf.add_module_info(
        "9.2 Mark Notification Read",
        "Mark individual notification as read.",
        "POST /storekeeper/api/notifications/<notification_id>/read",
        "POST",
        [
            "Update notification read status",
            "Remove from unread counter",
            "AJAX-based action"
        ]
    )
    pdf.ln(3)

    # WORKFLOW DIAGRAM
    pdf.chapter_title("STOREKEEPER WORKFLOW DIAGRAM")
    pdf.normal_text(
        "DAILY EQUIPMENT OPERATIONS:\n"
        "Equipment Available (On Campus) -> Recipient Requests\n"
        "                                         |\n"
        "                                 Issue Equipment\n"
        "                                         |\n"
        "                                Record IssuedEquipment\n"
        "                                         |\n"
        "                                   Generate Receipt\n"
        "\n\n"
        "RETURN & DAMAGE ASSESSMENT:\n"
        "Equipment Return -> Record Return Date\n"
        "                         |\n"
        "         +-------+-------+-------+\n"
        "         |       |       |       |\n"
        "       GOOD  DAMAGED   LOST  PARTIAL\n"
        "         |       |       |       |\n"
        "      Complete  Assess  Assess  Some Good\n"
        "         |       |       |       |\n"
        "      Clear?   Damaged? Lost?   Mixed\n"
        "        (End)      |       |       |\n"
        "                   +---+---+-------+\n"
        "                       |\n"
        "              Damage/Loss Status: Pending\n"
        "                       |\n"
        "         Storekeeper Reviews -> Can Fix?\n"
        "                       |              |\n"
        "                    YES -> CLEAR   NO -> ESCALATE\n"
        "                       |                  |\n"
        "                   Repaired/      Send to Admin\n"
        "                   Replaced            |\n"
        "                       |            Admin Reviews\n"
        "                       |               |\n"
        "                       +---+---+---+---+\n"
        "                           |       |   |\n"
        "                        Approve Reject Waive\n"
        "                           |       |\n"
        "                       Cleared Needs Review\n"
        "                           |       |\n"
        "                           |    Back to Storekeeper\n"
        "                           |       |\n"
        "                           +---+---+\n"
        "                               |\n"
        "                        Check Recipient Clearance\n"
        "                            (All items clear?)\n"
        "\n\n"
        "RECEIPT GENERATION:\n"
        "Issue Item -> Record IssuedEquipment -> Group by (Recipient, Date)\n"
        "                                            |\n"
        "                                   Same-day issuances\n"
        "                                   combined into ONE receipt\n"
        "                                            |\n"
        "                                   Receipt has equipment list\n"
        "                                   with total quantities\n"
        "\n\n"
        "ADMIN INTERACTION POINTS:\n"
        "Storekeeper Needs Review <-> Admin Reviews <-> Approve/Reject\n"
        "                                    |\n"
        "                                Escalated Items\n"
        "                                    |\n"
        "                            Admin sends back?\n"
        "                                    |\n"
        "                            Needs Review status\n"
        "                                    |\n"
        "                            Back to Storekeeper\n"
    )
    pdf.ln(3)

    # MODULE RELATIONSHIPS
    pdf.chapter_title("MODULE RELATIONSHIPS & DATA FLOW")
    pdf.normal_text(
        "Campus Equipment Inventory\n"
        "  |\n"
        "  +-> Equipment Availability Check\n"
        "       |\n"
        "       +-> Equipment Issuance\n"
        "            |\n"
        "            +-> Issue Receipt Generation\n"
        "                 |\n"
        "                 +-> Recipient Has IssuedEquipment Record\n"
        "                      |\n"
        "                      +-> Equipment Return Processing\n"
        "                           |\n"
        "                           +-> Return Condition Assessment\n"
        "                                |\n"
        "                 YES (Good?) -> Complete/Return\n"
        "                   |                       (End)\n"
        "                   |\n"
        "              NO (Damaged/Lost?)\n"
        "                   |\n"
        "                   +-> Damage/Loss Status: Pending\n"
        "                        |\n"
        "                        +-> Storekeeper Review\n"
        "                             |\n"
        "              Can Fix?  +-----+-+\n"
        "              YES  |           |  NO\n"
        "                   |           |\n"
        "                CLEAR      ESCALATE\n"
        "                   |           |\n"
        "              Repaired/    To Admin\n"
        "              Replaced        |\n"
        "                   |      Admin Reviews\n"
        "                   |      Approve/Reject\n"
        "                   |      Reject?\n"
        "                   |           |\n"
        "                   |      Needs Review\n"
        "                   |           |\n"
        "                   |    Back to Storekeeper\n"
        "                   |           |\n"
        "                   +-----+-----+\n"
        "                         |\n"
        "                   Status: Cleared\n"
        "                         |\n"
        "                Check if all recipient\n"
        "                items are cleared\n"
        "                         |\n"
        "              Recipient Clearance Status\n"
        "                  (Cleared/Pending/Overdue)\n"
        "\n"
        "Clearance Reporting\n"
        "  |\n"
        "  +-> View by Recipient\n"
        "  +-> View Status Summary\n"
        "  +-> Follow-up on Pending Items\n"
        "\n"
        "Notifications\n"
        "  |\n"
        "  +-> Admin escalates item\n"
        "  +-> Admin sends item back (Needs Review)\n"
        "  +-> New damage items to review\n"
        "  +-> Low stock alerts\n"
        "  +-> Due items reminders\n"
    )
    pdf.ln(5)

    # KEY METRICS & STATUS VALUES
    pdf.chapter_title("KEY METRICS & STATUS VALUES")
    pdf.normal_text(
        "EQUIPMENT STATUS VALUES:\n"
        "- Issued: Equipment given to recipient, awaiting return\n"
        "- Returned: Equipment returned, condition recorded\n"
        "- Partial Return: Some items returned, others pending\n"
        "\n"
        "RETURN CONDITIONS (per item):\n"
        "- Good: Equipment returned in acceptable condition\n"
        "- Damaged: Equipment damaged during use\n"
        "- Lost: Equipment not returned / lost\n"
        "- Partial: Some items in condition, others missing\n"
        "\n"
        "DAMAGE/LOSS CLEARANCE STATUS:\n"
        "- Pending: Item returned, awaiting storekeeper review\n"
        "- Needs Review: Admin rejected, needs storekeeper re-assessment\n"
        "- Escalated: Storekeeper unable to resolve, with admin\n"
        "- Repaired: Item was damaged, successfully repaired\n"
        "- Replaced: Item was lost/damaged, replacement issued\n"
        "- Cleared: Admin approved, item resolved\n"
        "- Waived: Admin waived requirement, item resolved\n"
        "\n"
        "RECIPIENT CLEARANCE STATUS:\n"
        "- Cleared: All items for recipient have clearance\n"
        "- Pending: One or more items awaiting clearance\n"
        "- Overdue: Clearance process delayed\n"
        "\n"
        "CAMPUS INVENTORY METRICS:\n"
        "- Total Equipment: All items distributed to campus\n"
        "- Available: Distributed minus currently issued\n"
        "- Low Stock: 5 or fewer items available\n"
        "- Issued Count: Currently outstanding items\n"
    )
    pdf.ln(3)

    # STOREKEEPER RESPONSIBILITIES
    pdf.chapter_title("STOREKEEPER RESPONSIBILITIES & WORKFLOW")
    pdf.normal_text(
        "DAILY OPERATIONS:\n"
        "1. Issue Equipment\n"
        "   - Verify recipient identity\n"
        "   - Check available inventory\n"
        "   - Record issuance with expected return date\n"
        "   - Generate receipt\n"
        "\n"
        "2. Process Returns\n"
        "   - Verify returned equipment\n"
        "   - Assess condition (Good/Damaged/Lost)\n"
        "   - Record condition details\n"
        "   - Update IssuedEquipment status\n"
        "\n"
        "3. Monitor Low Stock\n"
        "   - Check dashboard alerts\n"
        "   - Request distribution from admin if needed\n"
        "   - Manage campus inventory levels\n"
        "\n"
        "4. Track Due Items\n"
        "   - Review expected return dates\n"
        "   - Follow up with recipients\n"
        "   - Escalate overdue items to admin\n"
        "\n"
        "DAMAGE/LOSS REVIEW WORKFLOW:\n"
        "1. Item Returned with Damage/Loss\n"
        "   - Assessment stored in return_conditions JSON\n"
        "   - Status: Pending (awaiting review)\n"
        "\n"
        "2. Storekeeper Reviews Item\n"
        "   - Assess severity of damage\n"
        "   - Determine if item can be repaired\n"
        "   - Gather additional information if needed\n"
        "\n"
        "3. Storekeeper Decision\n"
        "   A) CLEAR if fixable\n"
        "      - Set status to Repaired or Replaced\n"
        "      - Document repair/replacement details\n"
        "      - Item resolved at this level\n"
        "\n"
        "   B) ESCALATE if unsure/unfixable\n"
        "      - Send to admin with assessment notes\n"
        "      - Set status to Escalated\n"
        "      - Wait for admin decision\n"
        "\n"
        "4. Admin Response\n"
        "   - Admin reviews storekeeper notes\n"
        "   - Approves (sets Cleared/Waived)\n"
        "   - OR Rejects (sets Needs Review)\n"
        "\n"
        "5. If Rejected (Needs Review)\n"
        "   - Back to storekeeper for re-assessment\n"
        "   - Item highlighted in yellow priority view\n"
        "   - Repeat review process\n"
        "\n"
        "CLEARANCE STATUS CHECKING:\n"
        "- After item cleared, system checks recipient status\n"
        "- If all recipient items cleared -> Recipient status: Cleared\n"
        "- If any items pending -> Recipient status: Pending\n"
        "- If overdue -> Status: Overdue\n"
        "\n"
        "REPORTING & FOLLOW-UP:\n"
        "1. View Clearance Report\n"
        "   - See all recipients issued by this storekeeper\n"
        "   - Check clearance status (Cleared/Pending/Overdue)\n"
        "   - Follow up on pending items\n"
        "\n"
        "2. Recipient Tracking\n"
        "   - Click on recipient to see all issued items\n"
        "   - Monitor clearance progress\n"
        "   - Contact recipient if needed\n"
    )

    # Save PDF
    output_path = "Sports_Equipment_Storekeeper_Panel_Documentation.pdf"
    pdf.output(output_path)
    print(f"[OK] PDF generated successfully: {output_path}")


if __name__ == "__main__":
    generate_storekeeper_pdf()
