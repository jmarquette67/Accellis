from flask import Blueprint, render_template, request, redirect, url_for, abort, flash
from sqlmodel import Session, select
from app.database import engine
from app.models import Client, Metric, Score, AuditLog, RoleType, User
from app.utils import current_user, role_required, manager_or_admin_required
from app.forms import build_score_form, ScoreEditForm

bp = Blueprint("scores", __name__, url_prefix="/scores")

@bp.route("/")
def score_list():
    """Display list of all client scores"""
    with Session(engine) as session:
        # Get all scores with client and metric information
        statement = select(Score, Client, Metric).join(Client).join(Metric).order_by(Score.taken_at.desc())
        results = session.exec(statement).all()
        
        scores = []
        for score, client, metric in results:
            scores.append({
                'id': score.id,
                'client_name': client.name,
                'metric_name': metric.name,
                'value': score.value,
                'taken_at': score.taken_at,
                'locked': score.locked
            })
    
    return render_template('scores/list.html', scores=scores)

@bp.route("/client/<int:client_id>")
def client_scores(client_id):
    """Display all scores for a specific client"""
    with Session(engine) as session:
        # Get client
        client = session.get(Client, client_id)
        if not client:
            abort(404)
        
        # Get client scores with metrics
        statement = select(Score, Metric).join(Metric).where(Score.client_id == client_id).order_by(Score.taken_at.desc())
        results = session.exec(statement).all()
        
        scores = []
        for score, metric in results:
            scores.append({
                'id': score.id,
                'metric_name': metric.name,
                'value': score.value,
                'taken_at': score.taken_at,
                'locked': score.locked,
                'status': 'high' if score.value >= metric.high_threshold else 'low' if score.value <= metric.low_threshold else 'medium'
            })
    
    return render_template('scores/client_scores.html', client=client, scores=scores)

@bp.route("/metric/<int:metric_id>")
def metric_scores(metric_id):
    """Display all scores for a specific metric across clients"""
    with Session(engine) as session:
        # Get metric
        metric = session.get(Metric, metric_id)
        if not metric:
            abort(404)
        
        # Get metric scores with clients
        statement = select(Score, Client).join(Client).where(Score.metric_id == metric_id).order_by(Score.taken_at.desc())
        results = session.exec(statement).all()
        
        scores = []
        for score, client in results:
            scores.append({
                'id': score.id,
                'client_name': client.name,
                'value': score.value,
                'taken_at': score.taken_at,
                'locked': score.locked,
                'status': 'high' if score.value >= metric.high_threshold else 'low' if score.value <= metric.low_threshold else 'medium'
            })
    
    return render_template('scores/metric_scores.html', metric=metric, scores=scores)

@bp.route("/unlock/<int:score_id>", methods=['POST'])
@manager_or_admin_required
def unlock_score(score_id):
    """Unlock a score for editing (Admin/Manager only)"""
    with Session(engine) as session:
        score = session.get(Score, score_id)
        if not score:
            abort(404)
        
        # Unlock the score
        score.locked = False
        session.add(score)
        session.commit()
        
        # Log the action
        user = current_user()
        audit_log = AuditLog(
            user_id=user.id,
            action="unlock_score",
            target_table="score",
            target_id=score_id
        )
        session.add(audit_log)
        session.commit()
        
        flash(f'Score unlocked successfully', 'success')
        return redirect(url_for('scores.client_scores', client_id=score.client_id))

@bp.route("/lock/<int:score_id>", methods=['POST'])
@manager_or_admin_required
def lock_score(score_id):
    """Lock a score (Admin/Manager only)"""
    with Session(engine) as session:
        score = session.get(Score, score_id)
        if not score:
            abort(404)
        
        # Lock the score
        score.locked = True
        session.add(score)
        session.commit()
        
        # Log the action
        user = current_user()
        audit_log = AuditLog(
            user_id=user.id,
            action="lock_score",
            target_table="score",
            target_id=score_id
        )
        session.add(audit_log)
        session.commit()
        
        flash(f'Score locked successfully', 'success')
        return redirect(url_for('scores.client_scores', client_id=score.client_id))

@bp.route("/new/<int:client_id>", methods=["GET", "POST"])
@role_required(RoleType.VCIO, RoleType.TAM, RoleType.MANAGER, RoleType.ADMIN)
def enter_scores(client_id):
    """Enter scores for all metrics for a specific client"""
    user = current_user()
    with Session(engine) as s:
        client = s.get(Client, client_id)
        if not client:
            abort(404)

        # allow only if user owns client OR elevated role
        if (user.role not in (RoleType.ADMIN, RoleType.MANAGER) and
                client_id not in [uc.client_id for uc in user.clients]):
            abort(403)

        metrics = s.exec(select(Metric).order_by(Metric.id)).all()
        ScoreForm = build_score_form(metrics)
        form = ScoreForm(request.form)

        if request.method == "POST" and form.validate():
            for m in metrics:
                field = getattr(form, f"metric_{m.id}")
                value = round(field.data)          # 0-100 whole numbers
                score = Score(client_id=client_id,
                              metric_id=m.id,
                              value=value,
                              locked=True)
                s.add(score)
                s.add(AuditLog(user_id=user.id,
                               action="CREATE",
                               target_table="score",
                               target_id=m.id))
            s.commit()
            flash(f'Scores entered successfully for {client.name}', 'success')
            return redirect(url_for("dashboard"))

        return render_template("app/score_form.html",
                               form=form, client=client)