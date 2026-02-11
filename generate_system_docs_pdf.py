#!/usr/bin/env python3
"""
Generate a PDF document of the Sports Equipment Management System
Operational Mechanism for Damage/Loss Clearance Review Workflow
"""

from fpdf import FPDF
from datetime import datetime


class SystemDocPDF(FPDF):
    def header(self):
        self.set_font("Arial", "B", 16)
        self.cell(0, 10, "Sports Equipment Management System", ln=True, align="C")
        self.set_font("Arial", "I", 12)
        self.cell(0, 10, "Operational Mechanism - Damage/Loss Clearance Review", ln=True, align="C")
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.cell(0, 10, f"Page {self.page_no()} | Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", align="C")

    def chapter_title(self, title):
        self.set_font("Arial", "B", 14)
        self.set_fill_color(0, 102, 204)
        self.set_text_color(255, 255, 255)
        self.cell(0, 10, title, ln=True, fill=True, align="L")
        self.set_text_color(0, 0, 0)
        self.ln(4)

    def chapter_heading(self, heading):
        self.set_font("Arial", "B", 11)
        self.cell(0, 8, heading, ln=True)
        self.ln(2)

    def normal_text(self, text):
        self.set_font("Arial", "", 10)
        self.multi_cell(0, 5, text)

    def table_header(self, headers, widths):
        self.set_font("Arial", "B", 9)
        self.set_fill_color(200, 200, 200)
        for header, width in zip(headers, widths):
            self.cell(width, 7, header, fill=True, border=1, align="C")
        self.ln()

    def table_row(self, items, widths):
        self.set_font("Arial", "", 9)
        for item, width in zip(items, widths):
            self.cell(width, 6, str(item)[:30], border=1, align="L")
        self.ln()


def generate_pdf():
    pdf = SystemDocPDF()
    pdf.add_page()
    
    # INTRODUCTION
    pdf.chapter_title("SYSTEM OVERVIEW")
    pdf.normal_text(
        "This document describes the complete operational mechanism for the Sports Equipment Management System, "
        "specifically the Damage/Loss Clearance Review workflow. The system manages equipment issuance, return, "
        "damage assessment, and clearance approval across Storekeeper and Admin roles."
    )
    pdf.ln(5)

    # PHASE 1
    pdf.chapter_title("PHASE 1: EQUIPMENT ISSUANCE & RETURN")
    
    pdf.chapter_heading("Step 1.1: Storekeeper Issues Equipment")
    pdf.normal_text(
        "Route: /storekeeper/issue\n"
        "- Equipment status: Issued\n"
        "- Record: issued_by = storekeeper payroll number\n"
        "- Serial numbers tracked (optional)"
    )
    pdf.ln(3)
    
    pdf.chapter_heading("Step 1.2: Equipment Returned with Conditions")
    pdf.normal_text(
        "Route: /storekeeper/return-equipment\n"
        "- Return conditions recorded: JSON with serial -> condition mapping\n"
        "- Conditions: Good, Damaged, Lost, or Partial Return\n"
        "- Status changes to: Returned or Partial Return\n"
        "- date_returned recorded"
    )
    pdf.ln(5)

    # PHASE 2
    pdf.chapter_title("PHASE 2: STOREKEEPER REVIEW")
    
    pdf.chapter_heading("Step 2.1: Storekeeper Accesses Damage View")
    pdf.normal_text(
        "Route: /storekeeper/damage-clearance\n"
        "- Shows: All returned equipment with Damaged/Lost conditions from their campus\n"
        "- Status filtering:\n"
        "  - Pending (default): No damage_clearance_status or status = 'Pending'\n"
        "  - Needs Review (yellow): Status = 'Needs Review' (sorted to top)\n"
        "  - Escalated: Hidden (already with admin)\n"
        "  - Cleared: Hidden (Repaired/Replaced/Waived)"
    )
    pdf.ln(3)
    
    pdf.chapter_heading("Step 2.2: Storekeeper Takes Action")
    pdf.normal_text(
        "Route: /storekeeper/damage-clearance/<issue_id> (POST)\n\n"
        "Two options available:\n\n"
        "1. CLEAR: Mark as Repaired or Replaced\n"
        "   - Status set to: Repaired or Replaced\n"
        "   - Notes recorded\n"
        "   - Item leaves storekeeper view\n"
        "   - Recipient may achieve clearance\n\n"
        "2. ESCALATE: Send to admin for further review\n"
        "   - Status set to: Escalated\n"
        "   - Notes sent to admin\n"
        "   - Item moves to admin escalated view\n"
        "   - Notification sent to admin dashboard"
    )
    pdf.ln(5)

    # PHASE 3
    pdf.chapter_title("PHASE 3: ADMIN REVIEW")
    
    pdf.chapter_heading("Step 3.1: Admin Accesses Escalated Items")
    pdf.normal_text(
        "Route: /admin/escalated-damage\n"
        "- Shows: Items with damage_clearance_status = 'Escalated'\n"
        "- For each item displays:\n"
        "  - Recipient info (Student/Staff)\n"
        "  - Equipment damaged/lost count\n"
        "  - Storekeeper notes\n"
        "  - Return conditions with serials\n"
        "  - Allows file upload (damage document)"
    )
    pdf.ln(3)
    
    pdf.chapter_heading("Step 3.2: Admin Takes Action")
    pdf.normal_text(
        "Route: /admin/escalated-damage/<issue_id> (POST)\n\n"
        "Three options available:\n\n"
        "1. CLEAR: Admin accepts damage/loss is resolved\n"
        "   - Status set to: Cleared\n"
        "   - Item exits system\n"
        "   - Contributes to recipient clearance\n\n"
        "2. WAIVE: Admin forgives the damage/loss\n"
        "   - Status set to: Waived\n"
        "   - Item waived from clearance requirement\n"
        "   - Recipient may clear despite damage\n\n"
        "3. REJECT: Admin sends back to storekeeper\n"
        "   - Status reverted to: Pending\n"
        "   - Admin notes appended: [Admin Rejected] {reason}\n"
        "   - Notification sent to storekeeper\n"
        "   - Storekeeper must re-evaluate and decide"
    )
    pdf.ln(5)

    # PHASE 4
    pdf.chapter_title("PHASE 4: STOREKEEPER RE-REVIEW (AFTER REJECT)")
    
    pdf.chapter_heading("Step 4.1: Storekeeper Sees Rejected Item")
    pdf.normal_text(
        "- Status: Pending (back in damage view)\n"
        "- Admin notes visible with [Admin Rejected] label and reason\n"
        "- Can now:\n"
        "  - Accept admin feedback and mark as Repaired/Replaced\n"
        "  - Disagree and escalate again for further admin review"
    )
    pdf.ln(3)
    
    pdf.chapter_heading("Step 4.2: Outcome")
    pdf.normal_text(
        "- Final decision made by storekeeper\n"
        "- Item either clears or returns to admin (loop possible)\n"
        "- Process continues until consensus reached"
    )
    pdf.ln(5)

    # PHASE 5
    pdf.chapter_title("PHASE 5: ADMIN ROLLBACK MECHANISM")
    
    pdf.chapter_heading("Step 5.1: Admin Initiates Rollback")
    pdf.normal_text(
        "Route: /admin/clearance/<recipient_id>/rollback (GET/POST)\n"
        "Purpose: Revert cleared/waived items back for storekeeper re-review\n"
        "Use case: Admin realizes a cleared item shouldn't have been cleared\n"
        "Allows bulk selection of returned items for review"
    )
    pdf.ln(3)
    
    pdf.chapter_heading("Step 5.2: Rollback Process")
    pdf.normal_text(
        "- Selected items marked: damage_clearance_status = 'Needs Review'\n"
        "- Notes appended: [Admin Rollback] {reason}\n"
        "- Clearance record status: Changed to Pending\n"
        "- Notification sent to affected storekeepers\n"
        "- Storekeeper directed to: /storekeeper/damage-clearance"
    )
    pdf.ln(3)
    
    pdf.chapter_heading("Step 5.3: Storekeeper Re-review")
    pdf.normal_text(
        "- Items appear in damage view with YELLOW HIGHLIGHT\n"
        "- Items sorted to TOP of list (Needs Review items first)\n"
        "- Storekeeper must re-evaluate and decide\n"
        "- Can clear (Repaired/Replaced) or escalate again"
    )
    pdf.ln(5)

    # PHASE 6
    pdf.chapter_title("PHASE 6: CLEARANCE STATUS DETERMINATION")
    
    pdf.chapter_heading("Recipient Clearance Status")
    pdf.normal_text(
        "Recipient's clearance status is determined by examining ALL issued items:\n\n"
        "IF all issued items are:\n"
        "  [OK] Returned (status = 'Returned')\n"
        "  [OK] AND have damage_clearance_status in:\n"
        "    ['Repaired', 'Replaced', 'Waived', 'Cleared']\n\n"
        "THEN clearance = CLEARED (recipient can receive certificate)\n\n"
        "ELSE IF any item has:\n"
        "  - damage_clearance_status = 'Escalated' OR 'Pending' OR 'Needs Review'\n\n"
        "THEN clearance = PENDING (waiting for resolution)\n\n"
        "Otherwise: clearance = OVERDUE"
    )
    pdf.ln(5)

    # STATUS TABLE
    pdf.chapter_title("STATUS VALUES & MEANINGS")
    pdf.ln(2)
    
    headers = ["Status", "Set By", "Visible To", "Next Action"]
    widths = [30, 25, 30, 30]
    pdf.table_header(headers, widths)
    
    statuses = [
        ["Pending", "System", "Storekeeper", "Clear/Escalate"],
        ["Needs Review", "Admin", "Storekeeper", "Clear/Escalate"],
        ["Repaired", "Storekeeper", "Admin", "Clearance OK"],
        ["Replaced", "Storekeeper", "Admin", "Clearance OK"],
        ["Escalated", "Storekeeper", "Admin", "Admin decides"],
        ["Cleared", "Admin", "System", "Clearance OK"],
        ["Waived", "Admin", "System", "Clearance OK"],
    ]
    
    for status in statuses:
        pdf.table_row(status, widths)
    
    pdf.ln(5)

    # FLOW DIAGRAM
    pdf.chapter_title("STATUS FLOW DIAGRAM")
    pdf.set_font("Arial", "", 9)
    pdf.normal_text(
        "ISSUANCE\n"
        "    |\n"
        "RETURN (with condition)\n"
        "    |\n"
        "STOREKEEPER REVIEW\n"
        "|--> [CLEAR] -> Repaired/Replaced ---> CLEARED\n"
        "|--> [ESCALATE] -> Escalated\n"
        "                    |\n"
        "            ADMIN ESCALATED VIEW\n"
        "            |--> [CLEAR] -> Cleared ---> CLEARED\n"
        "            |--> [WAIVE] -> Waived ---> CLEARED\n"
        "            |--> [REJECT] -> Pending\n"
        "                            |\n"
        "                    STOREKEEPER RE-REVIEW\n"
        "                    |--> [CLEAR] -> Repaired/Replaced ---> CLEARED\n"
        "                    |--> [ESCALATE] -> Escalated (loop)\n\n"
        "ADMIN ROLLBACK (ANY TIME)\n"
        "    |\n"
        "[Selected Items] -> Needs Review (yellow highlight)\n"
        "    |\n"
        "STOREKEEPER RE-REVIEW (as above)"
    )
    pdf.ln(5)

    # NOTIFICATIONS
    pdf.chapter_title("NOTIFICATION FLOW")
    
    headers = ["Event", "Recipient", "Message", "Route"]
    widths = [25, 20, 35, 35]
    pdf.table_header(headers, widths)
    
    notifications = [
        ["Escalate", "Admin", "Escalated by {sk}", "/admin/escalated-damage"],
        ["Reject", "Storekeeper", "Item rejected for review", "/storekeeper/damage-clearance"],
        ["Rollback", "Storekeeper", "{n} items marked for review", "/storekeeper/damage-clearance"],
    ]
    
    for notif in notifications:
        pdf.table_row(notif, widths)
    
    pdf.ln(5)

    # CLEARANCE COMPLETION
    pdf.chapter_title("CLEARANCE COMPLETION CRITERIA")
    pdf.normal_text(
        "A student/staff member achieves clearance (receives certificate) when:\n\n"
        "[OK] All equipment issued to them is returned\n"
        "[OK] All returned items have damage_clearance_status in:\n"
        "  ['Repaired', 'Replaced', 'Waived', 'Cleared']\n"
        "[OK] No items have status: Pending, Needs Review, or Escalated\n"
        "[OK] Clearance record status = 'Cleared'\n\n"
        "Once these conditions are met, the recipient's clearance is complete."
    )
    pdf.ln(5)

    # SUMMARY
    pdf.chapter_title("SYSTEM SUMMARY")
    pdf.normal_text(
        "The Sports Equipment Management System implements a collaborative review mechanism:\n\n"
        "1. STOREKEEPER ROLE: Issues equipment, records returns with conditions, makes initial "
        "damage assessment (clear or escalate)\n\n"
        "2. ADMIN ROLE: Reviews escalated items, makes final decisions (clear, waive, or reject), "
        "manages rollbacks, oversees clearance eligibility\n\n"
        "3. ITERATIVE PROCESS: If admin rejects, storekeeper re-reviews. If disagreed, can escalate "
        "again (bi-directional loop)\n\n"
        "4. CLEARANCE LOGIC: Recipient clears only when ALL items are resolved with final status. "
        "Admin can rollback at any time if needed.\n\n"
        "5. NOTIFICATIONS: Real-time alerts keep both roles informed of escalations, rejections, "
        "and rollbacks."
    )

    # Save PDF
    output_path = "c:\\xampp\\htdocs\\SportEquipmentSystem\\Sports_Equipment_System_Operational_Mechanism.pdf"
    pdf.output(output_path)
    print(f"[OK] PDF generated successfully: {output_path}")
    return output_path


if __name__ == "__main__":
    generate_pdf()
