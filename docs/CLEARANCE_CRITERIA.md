# Clearance Criteria and Implementation

## Overview
The clearance system determines whether students and staff members can be cleared based on their equipment borrowing history. The system evaluates equipment return status, condition, and timeliness.

## Clearance Criteria

### **CLEARED Status**
A recipient is considered **Cleared** when:
- **No equipment ever issued**: Recipients who have never borrowed any equipment are automatically cleared
- **All equipment returned AND all conditions satisfactory**:
  - All issued equipment has been returned (status = 'Returned')
  - All returned equipment is in 'Good' condition, OR
  - Any damaged/lost equipment has been marked as 'Replaced' by an administrator

### **PENDING Status**
A recipient has **Pending** clearance when:
- **Outstanding equipment**: Some equipment is still issued (not returned)
- **Damaged/lost equipment not replaced**: Equipment has been returned but is damaged/lost and hasn't been marked as replaced

### **OVERDUE Status**
A recipient is **Overdue** when:
- Equipment is still issued AND past the expected return date
- This takes precedence over other status checks

## Implementation Details

### Dynamic Status Calculation
The system uses a dynamic calculation function `get_clearance_status()` in `Utils/clearance_integration.py` that evaluates clearance status in real-time based on current database state.

### Equipment Return Conditions
Return conditions are stored as JSON in the `return_conditions` field of `IssuedEquipment`:
- `'{"condition": "Good"}'` - Equipment returned in good condition
- `'{"condition": "Damaged"}'` - Equipment returned damaged
- `'{"condition": "Lost"}'` - Equipment reported lost
- `'{"replaced": true}'` - Damaged/lost equipment has been replaced

### Administrative Actions
Administrators can:
1. **View clearance status** for all recipients via the clearance report
2. **Manage clearance** for individual students and staff
3. **Mark equipment as replaced** when damaged/lost items are substituted
4. **Process clearance** once all criteria are met

### Routes and Templates
- `/admin/clearance-report` - Main clearance status overview
- `/admin/clearance/<student_id>/manage` - Student clearance management
- `/admin/clearance/staff/<staff_payroll>/manage` - Staff clearance management
- `templates/clearance_report.html` - Status overview with summary cards
- `templates/clearance_manage.html` - Student clearance management interface
- `templates/clearance_manage_staff.html` - Staff clearance management interface

### Database Integration
- **Students**: Clearance status stored in `Clearance` table when manually processed
- **Staff**: Clearance evaluated dynamically (not stored in Clearance table)
- **Real-time updates**: Status reflects current equipment state immediately

## Status Priority
1. **Overdue** (highest priority - blocks all other clearance)
2. **Pending** (equipment issues exist)
3. **Cleared** (all criteria met)

## Benefits
- **Automated evaluation**: No manual status tracking required
- **Real-time accuracy**: Status updates immediately when equipment is returned
- **Flexible replacement handling**: Damaged/lost items can be cleared once replaced
- **Unified system**: Same criteria apply to both students and staff
- **Administrative control**: Manual intervention possible for edge cases</content>
<parameter name="filePath">c:\xampp\htdocs\SportEquipmentSystem\docs\CLEARANCE_CRITERIA.md