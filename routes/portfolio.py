from flask import Blueprint, render_template, request, jsonify
from models.portfolio import PortfolioTag, PortfolioGroup, PortfolioPerformance, Portfolio
from models.db import db
from datetime import datetime
from flask_login import current_user, login_required

portfolio = Blueprint('portfolio', __name__)

@portfolio.route('/portfolio/customize')
@login_required
def customize():
    portfolio_groups = PortfolioGroup.query.filter_by(user_id=current_user.id).all()
    portfolio_tags = PortfolioTag.query.filter_by(user_id=current_user.id).all()
    portfolios = Portfolio.query.filter_by(user_id=current_user.id).all()
    
    return render_template('portfolio/customize.html',
                         portfolio_groups=portfolio_groups,
                         portfolio_tags=portfolio_tags,
                         portfolios=portfolios)

@portfolio.route('/api/portfolio/groups', methods=['GET', 'POST'])
@login_required
def handle_groups():
    if request.method == 'POST':
        data = request.form
        group = PortfolioGroup(
            user_id=current_user.id,
            name=data['name'],
            description=data.get('description')
        )
        db.session.add(group)
        try:
            db.session.commit()
            return jsonify({'success': True, 'id': group.id})
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'error': str(e)})
            
    # GET method
    groups = PortfolioGroup.query.filter_by(user_id=current_user.id).all()
    return jsonify([{
        'id': g.id,
        'name': g.name,
        'description': g.description
    } for g in groups])

@portfolio.route('/api/portfolio/tags', methods=['GET', 'POST'])
@login_required
def handle_tags():
    if request.method == 'POST':
        data = request.form
        tag = PortfolioTag(
            user_id=current_user.id,
            name=data['name'],
            color=data.get('color', '#007bff')
        )
        db.session.add(tag)
        try:
            db.session.commit()
            return jsonify({'success': True, 'id': tag.id})
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'error': str(e)})
            
    # GET method
    tags = PortfolioTag.query.filter_by(user_id=current_user.id).all()
    return jsonify([{
        'id': t.id,
        'name': t.name,
        'color': t.color
    } for t in tags])

@portfolio.route('/api/portfolio/<int:portfolio_id>/performance', methods=['GET', 'POST'])
@login_required
def handle_performance(portfolio_id):
    if request.method == 'POST':
        data = request.form
        performance = PortfolioPerformance(
            portfolio_id=portfolio_id,
            total_value=data['total_value'],
            value_change=data.get('value_change'),
            change_percentage=data.get('change_percentage'),
            risk_score=data.get('risk_score')
        )
        db.session.add(performance)
        try:
            db.session.commit()
            return jsonify({'success': True, 'id': performance.id})
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'error': str(e)})
            
    # GET method
    performances = PortfolioPerformance.query.filter_by(portfolio_id=portfolio_id).order_by(
        PortfolioPerformance.measurement_date.desc()
    ).all()
    return jsonify([{
        'id': p.id,
        'total_value': float(p.total_value),
        'value_change': float(p.value_change) if p.value_change else None,
        'change_percentage': float(p.change_percentage) if p.change_percentage else None,
        'risk_score': p.risk_score,
        'date': p.measurement_date.isoformat()
    } for p in performances])
