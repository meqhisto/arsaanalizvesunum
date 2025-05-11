from flask import Blueprint, render_template, request, jsonify, current_app
from models.portfolio import Customer, Appointment, CustomerInteraction
from models.db import db
from datetime import datetime
from functools import wraps
from flask_login import current_user, login_required

crm = Blueprint('crm', __name__)

@crm.route('/dashboard')
@login_required
def dashboard():
    customers = Customer.query.filter_by(user_id=current_user.id).all()
    interactions = CustomerInteraction.query.join(Customer).filter(
        Customer.user_id == current_user.id
    ).order_by(CustomerInteraction.date.desc()).limit(10).all()
    
    return render_template('crm/dashboard.html', 
                         customers=customers,
                         interactions=interactions)

@crm.route('/api/customers', methods=['GET', 'POST'])
@login_required
def handle_customers():
    if request.method == 'POST':
        data = request.form
        customer = Customer(
            user_id=current_user.id,
            name=data['name'],
            email=data.get('email'),
            phone=data.get('phone'),
            company=data.get('company'),
            customer_type=data.get('customer_type', 'bireysel'),
            notes=data.get('notes')
        )
        db.session.add(customer)
        try:
            db.session.commit()
            return jsonify({'success': True, 'id': customer.id})
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'error': str(e)})
    
    # GET method
    customers = Customer.query.filter_by(user_id=current_user.id).all()
    return jsonify([{
        'id': c.id,
        'name': c.name,
        'email': c.email,
        'phone': c.phone,
        'company': c.company,
        'customer_type': c.customer_type
    } for c in customers])

@crm.route('/api/appointments', methods=['GET', 'POST'])
@login_required
def handle_appointments():
    if request.method == 'POST':
        data = request.form
        appointment = Appointment(
            user_id=current_user.id,
            customer_id=data['customer_id'],
            title=data['title'],
            description=data.get('description'),
            start_time=datetime.fromisoformat(data['start_time']),
            end_time=datetime.fromisoformat(data['end_time']),
            location=data.get('location'),
            reminder=data.get('reminder') == 'on',
            reminder_time=int(data.get('reminder_time', 30))
        )
        db.session.add(appointment)
        try:
            db.session.commit()
            return jsonify({'success': True, 'id': appointment.id})
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'error': str(e)})
    
    # GET method - for calendar
    start = request.args.get('start')
    end = request.args.get('end')
    
    appointments = Appointment.query.filter(
        Appointment.user_id == current_user.id
    )
    if start:
        appointments = appointments.filter(Appointment.start_time >= start)
    if end:
        appointments = appointments.filter(Appointment.end_time <= end)
    
    return jsonify([{
        'id': a.id,
        'title': a.title,
        'start': a.start_time.isoformat(),
        'end': a.end_time.isoformat(),
        'description': a.description,
        'location': a.location
    } for a in appointments.all()])

@crm.route('/api/interactions', methods=['POST'])
@login_required
def add_interaction():
    data = request.form
    interaction = CustomerInteraction(
        customer_id=data['customer_id'],
        interaction_type=data['interaction_type'],
        description=data['description'],
        outcome=data.get('outcome'),
        next_action=data.get('next_action'),
        next_action_date=datetime.fromisoformat(data['next_action_date']) if data.get('next_action_date') else None,
        created_by=current_user.id
    )
    db.session.add(interaction)
    try:
        db.session.commit()
        return jsonify({'success': True, 'id': interaction.id})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})
