from app import db
from flask_login import UserMixin
from datetime import datetime, date, timedelta
from sqlalchemy import func

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    first_name = db.Column(db.String(64), nullable=False)
    last_name = db.Column(db.String(64), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='employee')  # 'employee' or 'manager'
    pto_balance = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    time_entries = db.relationship('TimeEntry', foreign_keys='TimeEntry.user_id', backref='user', lazy=True, cascade='all, delete-orphan')
    pto_requests = db.relationship('PTORequest', foreign_keys='PTORequest.user_id', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

class TimeEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    clock_in = db.Column(db.DateTime, nullable=False)
    clock_out = db.Column(db.DateTime)
    clock_in_location = db.Column(db.String(200))
    clock_out_location = db.Column(db.String(200))
    clock_in_lat = db.Column(db.Float)
    clock_in_lng = db.Column(db.Float)
    clock_out_lat = db.Column(db.Float)
    clock_out_lng = db.Column(db.Float)
    break_start = db.Column(db.DateTime)
    break_end = db.Column(db.DateTime)
    break_duration_minutes = db.Column(db.Integer, default=30)
    status = db.Column(db.String(20), default='pending')  # 'pending', 'approved', 'rejected'
    notes = db.Column(db.Text)
    approved_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    approved_at = db.Column(db.DateTime)
    
    def __repr__(self):
        return f'<TimeEntry {self.id} - {self.user.username}>'
    
    @property
    def hours_worked(self):
        if self.clock_out:
            total_time = self.clock_out - self.clock_in
            # Subtract break time if applicable
            if self.break_start and self.break_end:
                break_time = self.break_end - self.break_start
                total_time -= break_time
            return round(total_time.total_seconds() / 3600, 2)
        return 0
    
    @property
    def is_on_break(self):
        return self.break_start and not self.break_end
    
    @property
    def has_taken_break(self):
        return self.break_start is not None
    
    @property
    def break_end_time(self):
        if self.break_start:
            return self.break_start + timedelta(minutes=self.break_duration_minutes)
        return None
    
    @property
    def date(self):
        return self.clock_in.date()

class PTORequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    days_requested = db.Column(db.Float, nullable=False)
    pto_type = db.Column(db.String(20), nullable=False)  # 'pto', 'uto'
    reason = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending')  # 'pending', 'approved', 'rejected'
    approved_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    approved_at = db.Column(db.DateTime)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<PTORequest {self.id} - {self.user.username}>'

class Company(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200))
    work_location_lat = db.Column(db.Float)
    work_location_lng = db.Column(db.Float)
    max_distance_meters = db.Column(db.Integer, default=100)  # Maximum distance from work location
    
    def __repr__(self):
        return f'<Company {self.name}>'
