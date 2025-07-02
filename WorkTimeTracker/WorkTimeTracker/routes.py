from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from datetime import datetime, date, timedelta
from models import User, TimeEntry, PTORequest, Company
from app import db
import math

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
@login_required
def dashboard():
    # Get current time entry (if clocked in)
    current_entry = TimeEntry.query.filter_by(
        user_id=current_user.id,
        clock_out=None
    ).first()
    
    # Get recent time entries
    recent_entries = TimeEntry.query.filter_by(
        user_id=current_user.id
    ).order_by(TimeEntry.clock_in.desc()).limit(5).all()
    
    # Get pending PTO requests
    pending_pto = PTORequest.query.filter_by(
        user_id=current_user.id,
        status='pending'
    ).count()
    
    # Calculate hours worked this week
    today = date.today()
    start_of_week = today - timedelta(days=today.weekday())
    week_entries = TimeEntry.query.filter(
        TimeEntry.user_id == current_user.id,
        TimeEntry.clock_in >= datetime.combine(start_of_week, datetime.min.time()),
        TimeEntry.clock_out.isnot(None)
    ).all()
    
    hours_this_week = sum([entry.hours_worked for entry in week_entries])
    
    return render_template('dashboard.html',
                         current_entry=current_entry,
                         recent_entries=recent_entries,
                         pending_pto=pending_pto,
                         hours_this_week=hours_this_week)

@main_bp.route('/timecard')
@login_required
def timecard():
    # Get time entries for current month
    today = date.today()
    start_of_month = date(today.year, today.month, 1)
    
    entries = TimeEntry.query.filter(
        TimeEntry.user_id == current_user.id,
        TimeEntry.clock_in >= datetime.combine(start_of_month, datetime.min.time())
    ).order_by(TimeEntry.clock_in.desc()).all()
    
    total_hours = sum([entry.hours_worked for entry in entries if entry.clock_out])
    
    return render_template('timecard.html', entries=entries, total_hours=total_hours)

@main_bp.route('/clock_in', methods=['POST'])
@login_required
def clock_in():
    # Check if user is already clocked in
    existing_entry = TimeEntry.query.filter_by(
        user_id=current_user.id,
        clock_out=None
    ).first()
    
    if existing_entry:
        flash('You are already clocked in.', 'warning')
        return redirect(url_for('main.dashboard'))
    
    # Get GPS coordinates
    lat = request.form.get('latitude')
    lng = request.form.get('longitude')
    location = request.form.get('location', 'Location unavailable')
    
    # Allow clock in without GPS but mark for admin review
    status = 'pending'
    if not lat or not lng:
        lat = None
        lng = None
        location = 'Location unavailable - Admin review required'
        status = 'review_required'
    
    # Verify location (if company location is set)
    company = Company.query.first()
    if company and company.work_location_lat and company.work_location_lng:
        distance = calculate_distance(
            float(lat), float(lng),
            company.work_location_lat, company.work_location_lng
        )
        
        if distance > company.max_distance_meters:
            flash(f'You are too far from the work location ({distance:.0f}m away). Please clock in from the workplace.', 'error')
            return redirect(url_for('main.dashboard'))
    
    # Create time entry
    time_entry = TimeEntry(
        user_id=current_user.id,
        clock_in=datetime.utcnow(),
        clock_in_location=location,
        clock_in_lat=float(lat) if lat else None,
        clock_in_lng=float(lng) if lng else None,
        status=status
    )
    
    db.session.add(time_entry)
    db.session.commit()
    
    flash('Successfully clocked in!', 'success')
    return redirect(url_for('main.dashboard'))

@main_bp.route('/start_break', methods=['POST'])
@login_required
def start_break():
    # Find current entry
    current_entry = TimeEntry.query.filter_by(
        user_id=current_user.id,
        clock_out=None
    ).first()
    
    if not current_entry:
        flash('You are not currently clocked in.', 'warning')
        return redirect(url_for('main.dashboard'))
    
    if current_entry.is_on_break:
        flash('You are already on a break.', 'warning')
        return redirect(url_for('main.dashboard'))
    
    if current_entry.has_taken_break:
        flash('You can only take one break per clock-in cycle.', 'warning')
        return redirect(url_for('main.dashboard'))
    
    # Start break
    current_entry.break_start = datetime.utcnow()
    current_entry.break_duration_minutes = int(request.form.get('duration', 30))
    
    db.session.commit()
    
    break_end_time = current_entry.break_end_time
    flash(f'Break started! See you back at {break_end_time.strftime("%I:%M %p")}.', 'info')
    return redirect(url_for('main.dashboard'))

@main_bp.route('/end_break', methods=['POST'])
@login_required
def end_break():
    # Find current entry on break
    current_entry = TimeEntry.query.filter_by(
        user_id=current_user.id,
        clock_out=None
    ).first()
    
    if not current_entry or not current_entry.is_on_break:
        flash('You are not currently on a break.', 'warning')
        return redirect(url_for('main.dashboard'))
    
    # End break
    current_entry.break_end = datetime.utcnow()
    current_entry.break_duration_minutes = round((current_entry.break_end - current_entry.break_start).seconds / 60, 2)
    
    db.session.commit()
    
    flash('Welcome back! Break ended successfully.', 'success')
    return redirect(url_for('main.dashboard'))

@main_bp.route('/clock_out', methods=['POST'])
@login_required
def clock_out():
    # Find current entry
    current_entry = TimeEntry.query.filter_by(
        user_id=current_user.id,
        clock_out=None
    ).first()
    
    if not current_entry:
        flash('You are not currently clocked in.', 'warning')
        return redirect(url_for('main.dashboard'))
    
    # If on break, end it first
    if current_entry.is_on_break:
        current_entry.break_end = datetime.utcnow()
    
    # Get GPS coordinates
    lat = request.form.get('latitude')
    lng = request.form.get('longitude')
    location = request.form.get('location', 'Location unavailable')
    
    # Allow clock out without GPS but mark for admin review
    if not lat or not lng:
        lat = None
        lng = None
        location = 'Location unavailable - Admin review required'
        if current_entry.status != 'review_required':
            current_entry.status = 'review_required'
    
    # Update time entry
    current_entry.clock_out = datetime.utcnow()
    current_entry.clock_out_location = location
    current_entry.clock_out_lat = float(lat) if lat else None
    current_entry.clock_out_lng = float(lng) if lng else None
    
    db.session.commit()
    
    flash(f'Successfully clocked out! You worked {current_entry.hours_worked:.2f} hours.', 'success')
    return redirect(url_for('main.dashboard'))

@main_bp.route('/pto')
@login_required
def pto():
    # Get PTO requests
    pto_requests = PTORequest.query.filter_by(
        user_id=current_user.id
    ).order_by(PTORequest.submitted_at.desc()).all()
    
    return render_template('pto.html', pto_requests=pto_requests)

@main_bp.route('/pto/request', methods=['POST'])
@login_required
def request_pto():
    start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d').date()
    end_date = datetime.strptime(request.form.get('end_date'), '%Y-%m-%d').date()
    pto_type = request.form.get('pto_type')
    reason = request.form.get('reason', '')
    
    # Calculate days requested (excluding weekends)
    days_requested = calculate_business_days(start_date, end_date)
    
    # Check if user has enough PTO balance (only for PTO requests, not UTO)
    if pto_type == 'pto' and days_requested > current_user.pto_balance:
        flash(f'Insufficient PTO balance. You requested {days_requested} days but only have {current_user.pto_balance} days available.', 'error')
        return redirect(url_for('main.pto'))
    
    # Create PTO request
    pto_request = PTORequest(
        user_id=current_user.id,
        start_date=start_date,
        end_date=end_date,
        days_requested=days_requested,
        pto_type=pto_type,
        reason=reason
    )
    
    db.session.add(pto_request)
    db.session.commit()
    
    flash(f'PTO request submitted for {days_requested} days.', 'success')
    return redirect(url_for('main.pto'))

@main_bp.route('/admin')
@login_required
def admin():
    if current_user.role != 'manager':
        flash('Access denied. Manager privileges required.', 'error')
        return redirect(url_for('main.dashboard'))
    
    # Get pending time entries (including review required)
    pending_timecards = TimeEntry.query.filter(
        TimeEntry.status.in_(['pending', 'review_required'])
    ).order_by(TimeEntry.clock_in.desc()).all()
    
    # Get pending PTO requests
    pending_pto_requests = PTORequest.query.filter_by(status='pending').order_by(PTORequest.submitted_at.desc()).all()
    
    # Get all employees and managers
    employees = User.query.filter_by(role='employee').all()
    managers = User.query.filter_by(role='manager').all()
    
    return render_template('admin.html',
                         pending_timecards=pending_timecards,
                         pending_pto_requests=pending_pto_requests,
                         employees=employees,
                         managers=managers)

@main_bp.route('/admin/approve_timecard/<int:entry_id>')
@login_required
def approve_timecard(entry_id):
    if current_user.role != 'manager':
        flash('Access denied.', 'error')
        return redirect(url_for('main.dashboard'))
    
    entry = TimeEntry.query.get_or_404(entry_id)
    entry.status = 'approved'
    entry.approved_by = current_user.id
    entry.approved_at = datetime.utcnow()
    
    db.session.commit()
    
    flash('Timecard approved successfully.', 'success')
    return redirect(url_for('main.admin'))

@main_bp.route('/admin/reject_timecard/<int:entry_id>')
@login_required
def reject_timecard(entry_id):
    if current_user.role != 'manager':
        flash('Access denied.', 'error')
        return redirect(url_for('main.dashboard'))
    
    entry = TimeEntry.query.get_or_404(entry_id)
    entry.status = 'rejected'
    entry.approved_by = current_user.id
    entry.approved_at = datetime.utcnow()
    
    db.session.commit()
    
    flash('Timecard rejected.', 'warning')
    return redirect(url_for('main.admin'))

@main_bp.route('/admin/approve_pto/<int:request_id>')
@login_required
def approve_pto(request_id):
    if current_user.role != 'manager':
        flash('Access denied.', 'error')
        return redirect(url_for('main.dashboard'))
    
    pto_request = PTORequest.query.get_or_404(request_id)
    pto_request.status = 'approved'
    pto_request.approved_by = current_user.id
    pto_request.approved_at = datetime.utcnow()
    
    # Deduct from user's PTO balance (only for PTO, not UTO)
    user = User.query.get(pto_request.user_id)
    if pto_request.pto_type == 'pto':
        user.pto_balance -= pto_request.days_requested
    
    db.session.commit()
    
    if pto_request.pto_type == 'pto':
        flash(f'PTO request approved. {pto_request.days_requested} days deducted from {user.full_name}\'s balance.', 'success')
    else:
        flash(f'UTO request approved for {user.full_name}. No balance deduction for unpaid time off.', 'success')
    return redirect(url_for('main.admin'))

@main_bp.route('/admin/reject_pto/<int:request_id>')
@login_required
def reject_pto(request_id):
    if current_user.role != 'manager':
        flash('Access denied.', 'error')
        return redirect(url_for('main.dashboard'))
    
    pto_request = PTORequest.query.get_or_404(request_id)
    pto_request.status = 'rejected'
    pto_request.approved_by = current_user.id
    pto_request.approved_at = datetime.utcnow()
    
    db.session.commit()
    
    flash('PTO request rejected.', 'warning')
    return redirect(url_for('main.admin'))

@main_bp.route('/admin/promote_user/<int:user_id>')
@login_required
def promote_user(user_id):
    if current_user.role != 'manager':
        flash('Access denied. Manager privileges required.', 'error')
        return redirect(url_for('main.dashboard'))
    
    user = User.query.get_or_404(user_id)
    
    if user.role == 'employee':
        user.role = 'manager'
        db.session.commit()
        flash(f'{user.full_name} has been promoted to manager.', 'success')
    else:
        flash(f'{user.full_name} is already a manager.', 'warning')
    
    return redirect(url_for('main.admin'))

@main_bp.route('/admin/demote_user/<int:user_id>')
@login_required
def demote_user(user_id):
    if current_user.role != 'manager':
        flash('Access denied. Manager privileges required.', 'error')
        return redirect(url_for('main.dashboard'))
    
    user = User.query.get_or_404(user_id)
    
    # Prevent demoting yourself
    if user.id == current_user.id:
        flash('You cannot demote yourself.', 'error')
        return redirect(url_for('main.admin'))
    
    if user.role == 'manager':
        user.role = 'employee'
        db.session.commit()
        flash(f'{user.full_name} has been demoted to employee.', 'success')
    else:
        flash(f'{user.full_name} is already an employee.', 'warning')
    
    return redirect(url_for('main.admin'))

@main_bp.route('/admin/delete_user/<int:user_id>')
@login_required
def delete_user(user_id):
    if current_user.role != 'manager':
        flash('Access denied. Manager privileges required.', 'error')
        return redirect(url_for('main.dashboard'))
    
    user = User.query.get_or_404(user_id)
    
    # Prevent deleting yourself
    if user.id == current_user.id:
        flash('You cannot delete your own account.', 'error')
        return redirect(url_for('main.admin'))
    
    # Delete the user (cascade will handle related records)
    db.session.delete(user)
    db.session.commit()
    
    flash(f'{user.full_name} has been removed from the system.', 'success')
    return redirect(url_for('main.admin'))

@main_bp.route('/account')
@login_required
def account():
    return render_template('account.html')


def calculate_distance(lat1, lng1, lat2, lng2):
    """Calculate distance between two GPS coordinates in meters."""
    R = 6371000  # Earth's radius in meters
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lng = math.radians(lng2 - lng1)
    
    a = (math.sin(delta_lat / 2) * math.sin(delta_lat / 2) +
         math.cos(lat1_rad) * math.cos(lat2_rad) *
         math.sin(delta_lng / 2) * math.sin(delta_lng / 2))
    
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    distance = R * c
    return distance

def calculate_business_days(start_date, end_date):
    """Calculate number of business days between two dates."""
    current_date = start_date
    business_days = 0
    
    while current_date <= end_date:
        if current_date.weekday() < 5:  # Monday to Friday
            business_days += 1
        current_date += timedelta(days=1)
    
    return business_days
