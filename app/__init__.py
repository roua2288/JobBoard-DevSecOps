import functools
import json
import logging
import os
import secrets
import sqlite3
import pymysql
from .mysql_db import MySQLDatabase
import time
import uuid
from collections import defaultdict
from pathlib import Path
from flask import Flask, abort, g, jsonify, redirect, render_template, request, send_file, session, url_for, flash
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.exceptions import HTTPException
from pypdf import PdfReader

SCHEMA = '''
CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY,name TEXT NOT NULL,email TEXT UNIQUE NOT NULL,password TEXT NOT NULL,role TEXT NOT NULL CHECK(role IN ('candidate','recruiter','admin')),active INTEGER NOT NULL DEFAULT 1);
CREATE TABLE IF NOT EXISTS jobs(id INTEGER PRIMARY KEY,title TEXT NOT NULL,company TEXT NOT NULL,location TEXT NOT NULL,contract TEXT NOT NULL,description TEXT NOT NULL,owner INTEGER NOT NULL REFERENCES users(id),status TEXT NOT NULL DEFAULT 'pending',created TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS cvs(id INTEGER PRIMARY KEY,owner INTEGER NOT NULL REFERENCES users(id),path TEXT NOT NULL,original TEXT NOT NULL,created TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS applications(id INTEGER PRIMARY KEY,job INTEGER NOT NULL REFERENCES jobs(id),candidate INTEGER NOT NULL REFERENCES users(id),cv INTEGER NOT NULL REFERENCES cvs(id),status TEXT DEFAULT 'En cours',created TEXT DEFAULT CURRENT_TIMESTAMP,UNIQUE(job,candidate));
CREATE TABLE IF NOT EXISTS cv_profiles(owner INTEGER PRIMARY KEY REFERENCES users(id),data TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY,actor INTEGER,event TEXT NOT NULL,target TEXT,correlation TEXT NOT NULL,created TEXT DEFAULT CURRENT_TIMESTAMP);
'''

def create_app(config=None):
    app=Flask(__name__)
    app.config.update(SECRET_KEY=os.environ.get('SECRET_KEY'),DATABASE=os.environ.get('DATABASE','instance/jobboard.db'),UPLOAD_FOLDER=os.environ.get('UPLOAD_FOLDER','instance/cvs'),MAX_CONTENT_LENGTH=2*1024*1024,SESSION_COOKIE_HTTPONLY=True,SESSION_COOKIE_SAMESITE='Lax',SESSION_COOKIE_SECURE=os.environ.get('COOKIE_SECURE','0')=='1',LAB_MODE=os.environ.get('LAB_MODE','0')=='1',TESTING=False)
    app.config.update(DB_ENGINE=os.environ.get('DB_ENGINE','sqlite'),DB_HOST=os.environ.get('DB_HOST','127.0.0.1'),DB_PORT=os.environ.get('DB_PORT','3306'),DB_NAME=os.environ.get('DB_NAME','jobboard'),DB_USER=os.environ.get('DB_USER','root'),DB_PASSWORD=os.environ.get('DB_PASSWORD',''))
    if config: app.config.update(config)
    if not app.config['SECRET_KEY']: raise RuntimeError('Définir SECRET_KEY avec une valeur aléatoire avant de démarrer.')
    Path(app.config['DATABASE']).parent.mkdir(parents=True,exist_ok=True)
    Path(app.config['UPLOAD_FOLDER']).mkdir(parents=True,exist_ok=True)
    app.logger.setLevel(logging.INFO)
    attempts=defaultdict(list)
    def db():
        if 'db' not in g:
            if app.config['DB_ENGINE']=='mysql':g.db=MySQLDatabase(app.config)
            else:
                g.db=sqlite3.connect(app.config['DATABASE']);g.db.row_factory=sqlite3.Row;g.db.execute('PRAGMA foreign_keys=ON');g.db.execute('PRAGMA busy_timeout=5000')
        return g.db
    @app.teardown_appcontext
    def close(_):
        if 'db' in g:g.db.close()
    def event(kind,target=''):
        actor=g.user['id'] if getattr(g,'user',None) else None
        db().execute('INSERT INTO events(actor,event,target,correlation) VALUES(?,?,?,?)',(actor,kind,str(target),g.correlation));db().commit()
        app.logger.info(json.dumps(dict(event=kind,actor=actor,target=str(target),correlation_id=g.correlation)))
    def require(*roles):
        def decorator(fn):
            @functools.wraps(fn)
            def wrapped(*args,**kwargs):
                if not g.user:return redirect(url_for('login'))
                if roles and g.user['role'] not in roles:event('access_denied',request.endpoint);abort(403)
                return fn(*args,**kwargs)
            return wrapped
        return decorator
    @app.before_request
    def before():
        g.correlation=uuid.uuid4().hex
        g.user=db().execute('SELECT * FROM users WHERE id=? AND active=1',(session.get('uid'),)).fetchone()
        session.setdefault('csrf',secrets.token_urlsafe(32))
        if request.method in ('POST','PUT','PATCH','DELETE') and request.endpoint != 'profile':
            token=request.form.get('csrf') or request.headers.get('X-CSRF-Token','')
            if not secrets.compare_digest(token,session['csrf']):event('csrf_rejected');abort(400,description='Jeton de formulaire invalide. Rechargez la page.')
    @app.after_request
    def headers(response):
        response.headers.update({'X-Content-Type-Options':'nosniff','X-Frame-Options':'DENY','Referrer-Policy':'same-origin','Content-Security-Policy':"default-src 'self'; style-src 'self'; script-src 'self'; img-src 'self' data:; object-src 'none'; base-uri 'self'; frame-ancestors 'none'; form-action 'self'",'Cache-Control':'no-store','X-Correlation-ID':g.correlation})
        if app.config['SESSION_COOKIE_SECURE']:response.headers['Strict-Transport-Security']='max-age=31536000'
        if app.config['LAB_MODE'] and request.path.startswith('/lab/'):
            response.headers.pop('Content-Security-Policy',None)
        return response
    @app.context_processor
    def context():return dict(user=getattr(g,'user',None),csrf=session.get('csrf'),lab=app.config['LAB_MODE'])
    @app.errorhandler(HTTPException)
    def error(e):return render_template('error.html',error=e),e.code
    @app.route('/health')
    def health():db().execute('SELECT 1');return jsonify(status='healthy')
    @app.get('/lab/session-key')
    def expose_session_key():
        return jsonify(signing_key=app.config['SECRET_KEY'])
    @app.route('/register',methods=['GET','POST'])
    def register():
        if request.method=='POST':
            name=request.form.get('name','').strip();email=request.form.get('email','').strip().lower();password=request.form.get('password','');role=request.form.get('role')
            if password!=request.form.get('confirm'):abort(400,description='Les deux mots de passe ne correspondent pas.')
            if not name or len(name)>100 or '@' not in email or len(email)>254 or len(password)<12 or len(password)>128 or role not in ('candidate','recruiter','admin'):abort(400,description='Nom et email valides, rôle autorisé et mot de passe de 12 à 128 caractères requis.')
            try:db().execute('INSERT INTO users(name,email,password,role) VALUES(?,?,?,?)',(name,email,generate_password_hash(password),role));db().commit()
            except (sqlite3.IntegrityError,pymysql.IntegrityError):abort(400,description='Inscription impossible avec ces informations.')
            event('registration');flash('Compte créé. Connectez-vous.');return redirect(url_for('login'))
        return render_template('auth.html',register=True)
    @app.route('/login',methods=['GET','POST'])
    def login():
        if request.method=='POST':
            # Process-local rate limit; use a shared limiter at the ingress for multiple replicas.
            ip=request.remote_addr or 'unknown';now=time.monotonic();attempts[ip]=[t for t in attempts[ip] if now-t<300]
            attempts[ip].append(now)
            u=db().execute('SELECT * FROM users WHERE email=? AND active=1',(request.form.get('email','').strip().lower(),)).fetchone()
            if not u or not check_password_hash(u['password'],request.form.get('password','')):event('login_failed');flash('Identifiants incorrects.');return render_template('auth.html',register=False),401
            session.clear();session['uid']=u['id'];session['csrf']=secrets.token_urlsafe(32);g.user=u;event('login_success');attempts.pop(ip,None);return redirect(url_for('dashboard'))
        return render_template('auth.html',register=False)
    @app.post('/logout')
    def logout():session.clear();return redirect(url_for('index'))
    @app.route('/')
    def index():
        q=request.args.get('q','')[:120]
        sql = "SELECT * FROM jobs WHERE status='active' AND title LIKE ?"
        jobs = db().execute(sql, (f"%{q}%",)).fetchall()
        return render_template('jobs.html', jobs=jobs, q=q)
    @app.route('/jobs/<int:job_id>')
    def job_detail(job_id):
        job=db().execute('SELECT * FROM jobs WHERE id=?',(job_id,)).fetchone()
        if not job:abort(404)
        if job['status']!='active' and not(g.user and(g.user['role']=='admin' or g.user['id']==job['owner'])):abort(404)
        cvs=db().execute('SELECT * FROM cvs WHERE owner=? ORDER BY id DESC',(g.user['id'],)).fetchall() if g.user else []
        applied=db().execute('SELECT id FROM applications WHERE candidate=? AND job=?',(g.user['id'],job_id)).fetchone() if g.user else None
        return render_template('detail.html',job=job,cvs=cvs,applied=applied)
    @app.route('/dashboard')
    @require()
    def dashboard():
        role=g.user['role'];uid=g.user['id']
        if role=='candidate':
            applications=db().execute('SELECT a.*,j.title,j.company FROM applications a JOIN jobs j ON j.id=a.job WHERE candidate=? ORDER BY a.id DESC',(uid,)).fetchall()
            cvs=db().execute('SELECT * FROM cvs WHERE owner=? ORDER BY id DESC',(uid,)).fetchall()
            return render_template('candidate.html',applications=applications,cvs=cvs)
        if role=='recruiter':
            jobs=db().execute('SELECT j.*, (SELECT count(*) FROM applications a WHERE a.job=j.id) total FROM jobs j WHERE owner=? ORDER BY id DESC',(uid,)).fetchall()
            applications=db().execute('SELECT a.*,j.title,u.name,c.original FROM applications a JOIN jobs j ON j.id=a.job JOIN users u ON u.id=a.candidate JOIN cvs c ON c.id=a.cv WHERE j.owner=? ORDER BY a.id DESC',(uid,)).fetchall()
            return render_template('recruiter.html',jobs=jobs,applications=applications)
        return render_template('admin.html',users=db().execute('SELECT id,name,email,role,active FROM users').fetchall(),jobs=db().execute('SELECT * FROM jobs ORDER BY id DESC').fetchall(),events=db().execute('SELECT * FROM events ORDER BY id DESC LIMIT 50').fetchall())
    @app.get('/metrics')
    @require('admin')
    def metrics():
        rows=db().execute('SELECT event,count(*) total FROM events GROUP BY event').fetchall()
        body='# HELP jobboard_security_events_total Recorded security events.\n# TYPE jobboard_security_events_total counter\n'
        for row in rows:
            body+='jobboard_security_events_total{event="'+row['event']+'"} '+str(row['total'])+'\n'
        return app.response_class(body,mimetype='text/plain')
    @app.route('/profile',methods=['GET','POST'])
    @require()
    def profile():
        if request.method=='POST':
            name=request.form.get('name','').strip();email=request.form.get('email','').strip().lower()
            if not name or len(name)>100 or '@' not in email or len(email)>254:abort(400)
            try:
                db().execute('UPDATE users SET name=?,email=? WHERE id=?',(name,email,g.user['id']));db().commit()
            except (sqlite3.IntegrityError,pymysql.IntegrityError):abort(400,description='Impossible de mettre à jour ce profil.')
            event('profile_updated');flash('Profil enregistré.');return redirect(url_for('profile'))
        return render_template('profile.html')
    @app.route('/jobs/new',methods=['GET','POST'])
    @require('recruiter')
    def new_job():
        if request.method=='POST':
            vals=[request.form.get(k,'').strip() for k in ('title','company','location','contract','description')]
            if any(not v for v in vals) or any(len(v)>200 for v in vals[:4]) or len(vals[4])>10000:abort(400)
            db().execute('INSERT INTO jobs(title,company,location,contract,description,owner) VALUES(?,?,?,?,?,?)',(*vals,g.user['id']));db().commit();event('job_created');flash('Offre envoyée pour validation.');return redirect(url_for('dashboard'))
        return render_template('new_job.html')
    @app.post('/jobs/<int:job_id>/close')
    @require('recruiter')
    def close_job(job_id):
        j=db().execute('SELECT * FROM jobs WHERE id=?',(job_id,)).fetchone()
        if not j:abort(404)
        if j['owner']!=g.user['id']:event('access_denied','job_close');abort(403)
        db().execute("UPDATE jobs SET status='closed' WHERE id=?",(job_id,));db().commit();event('job_closed',job_id);return redirect(url_for('dashboard'))
    @app.route('/cv/create',methods=['GET','POST'])
    @require('candidate')
    def create_cv():
        from .cv_builder import FIELDS, generate_cv
        row=db().execute('SELECT data FROM cv_profiles WHERE owner=?',(g.user['id'],)).fetchone()
        draft=json.loads(row['data']) if row else dict(name=g.user['name'],email=g.user['email'])
        if request.method=='POST':
            draft={k:request.form.get(k,'').strip() for k in FIELDS}
            if any(len(draft[k])>limit for k,(_,limit) in FIELDS.items()) or not draft['name'] or '@' not in draft['email']:
                abort(400,description='Vérifiez les champs obligatoires et les longueurs autorisées.')
            action=request.form.get('action')
            if action not in ('draft','download','save'):abort(400)
            encoded=json.dumps(draft,ensure_ascii=False)
            if row:db().execute('UPDATE cv_profiles SET data=? WHERE owner=?',(encoded,g.user['id']))
            else:db().execute('INSERT INTO cv_profiles(owner,data) VALUES(?,?)',(g.user['id'],encoded))
            db().commit()
            if action=='draft':
                flash('Brouillon du CV enregistré.');return redirect(url_for('create_cv'))
            pdf=generate_cv(draft)
            if action=='download':
                import io
                return send_file(io.BytesIO(pdf),as_attachment=True,download_name='Mon_CV.pdf',mimetype='application/pdf')
            filename=uuid.uuid4().hex+'.pdf'
            path=Path(app.config['UPLOAD_FOLDER'],filename);path.write_bytes(pdf)
            try:
                db().execute('INSERT INTO cvs(owner,path,original) VALUES(?,?,?)',(g.user['id'],filename,'Mon_CV.pdf'));db().commit()
            except Exception:
                path.unlink(missing_ok=True);raise
            event('cv_created')
            flash('CV créé et enregistré. Vous pouvez le sélectionner pour postuler.')
            return redirect(url_for('dashboard'))
        return render_template('cv_builder.html',draft=draft,fields=FIELDS)
    def validated_pdf(f):
        if not f or not f.filename or not f.filename.lower().endswith('.pdf'):abort(400,description='Un CV au format PDF est requis.')
        return f.read()
    def store_cv(data):
        path = Path(app.config['UPLOAD_FOLDER'], uuid.uuid4().hex + '.pdf')
        try:
            path.write_bytes(data)
            cv_id = db().execute(
                'INSERT INTO cvs(owner,path,original) VALUES(?,?,?)',
                (g.user['id'], path.name, 'CV.pdf'),
            ).lastrowid
        except Exception:
            path.unlink(missing_ok=True)
            raise
        return cv_id, path
    @app.post('/cv/upload')
    @require('candidate')
    def upload():
        _, path = store_cv(validated_pdf(request.files.get('cv')))
        try:
            db().commit()
        except Exception:
            path.unlink(missing_ok=True)
            raise
        event('cv_uploaded');flash('CV enregistré dans votre espace privé.');return redirect(url_for('dashboard'))
    @app.get('/cv/<int:cv_id>')
    @require()
    def cv_download(cv_id):
        cv=db().execute('SELECT * FROM cvs WHERE id=?',(cv_id,)).fetchone()
        if not cv:abort(404)
        event('cv_downloaded',cv_id);return send_file(Path(app.config['UPLOAD_FOLDER']).resolve()/cv['path'],as_attachment=True,download_name='CV.pdf',mimetype='application/pdf')
    @app.post('/jobs/<int:job_id>/apply')
    @require('candidate')
    def apply(job_id):
        j=db().execute("SELECT * FROM jobs WHERE id=? AND status='active'",(job_id,)).fetchone()
        if not j:abort(404)
        file = request.files.get('cv_file')
        path = None
        if file and file.filename:
            cv_id, path = store_cv(validated_pdf(file))
        else:
            cv = db().execute('SELECT id FROM cvs WHERE id=? AND owner=?',(request.form.get('cv'),g.user['id'])).fetchone()
            if not cv:
                abort(400, description='Choisissez un CV enregistré ou joignez un PDF.')
            cv_id = cv['id']
        try:
            db().execute('INSERT INTO applications(job,candidate,cv) VALUES(?,?,?)',(job_id,g.user['id'],cv_id))
            db().commit()
        except Exception as error:
            if path is not None:
                path.unlink(missing_ok=True)
            if isinstance(error, (sqlite3.IntegrityError, pymysql.IntegrityError)):
                abort(409, description='Vous avez déjà postulé à cette offre.')
            raise
        event('application_created',job_id);flash('Candidature envoyée.');return redirect(url_for('dashboard'))
    @app.post('/applications/<int:application_id>/withdraw')
    @require('candidate')
    def withdraw_application(application_id):
        result = db().execute(
            'DELETE FROM applications WHERE id=? AND candidate=?',
            (application_id, g.user['id']),
        )
        if not result.rowcount:
            abort(404)
        db().commit()
        event('application_withdrawn', application_id)
        flash('Candidature retirée. Votre CV reste dans vos documents.')
        return redirect(url_for('dashboard'))
    @app.post('/applications/<int:application_id>/status')
    @require('recruiter')
    def application_status(application_id):
        a=db().execute('SELECT a.id,j.owner FROM applications a JOIN jobs j ON j.id=a.job WHERE a.id=?',(application_id,)).fetchone()
        if not a:abort(404)
        if a['owner']!=g.user['id']:event('access_denied','application');abort(403)
        status=request.form.get('status')
        if status not in ('En cours','Entretien','Acceptée','Refusée'):abort(400)
        db().execute('UPDATE applications SET status=? WHERE id=?',(status,application_id));db().commit();event('application_status_changed',application_id);return redirect(url_for('dashboard'))
    @app.post('/admin/jobs/<int:job_id>')
    @require('admin')
    def moderate(job_id):
        status=request.form.get('status')
        if status not in ('active','rejected'):abort(400)
        db().execute('UPDATE jobs SET status=? WHERE id=?',(status,job_id));db().commit();event('job_moderated',job_id);return redirect(url_for('dashboard'))
    @app.post('/admin/users/<int:user_id>')
    @require('admin')
    def toggle_user(user_id):
        if user_id==g.user['id']:abort(400,description='Vous ne pouvez pas désactiver votre propre compte.')
        db().execute("UPDATE users SET active=1-active WHERE id=? AND role!='admin'",(user_id,));db().commit();event('user_toggled',user_id);return redirect(url_for('dashboard'))
    if app.config['LAB_MODE']:
        from .lab import register_lab
        register_lab(app,db,event,require)
    @app.cli.command('init-db')
    def init_db():
        db().executescript((Path(__file__).parent/'mysql_tables.sql').read_text() if app.config['DB_ENGINE']=='mysql' else SCHEMA)
        admin_password=os.environ.get('ADMIN_PASSWORD')
        if admin_password and not app.config['TESTING']:
            db().execute('INSERT OR IGNORE INTO users(name,email,password,role) VALUES(?,?,?,?)',('Administrateur','admin@gmail.com',generate_password_hash(admin_password),'admin'))
        db().commit();print('Base initialisée.')
    @app.cli.command('seed')
    def seed():
        password=os.environ.get('DEMO_PASSWORD')
        if not password or len(password)<12:raise RuntimeError('Définir DEMO_PASSWORD (12 caractères minimum).')
        for name,email,role in [('Roua Ben Amor','roua@example.test','candidate'),('Ahmed Lakti','ahmed@example.test','recruiter'),('Administrateur','admin@gmail.com','admin'),('Recruteur indépendant','other@example.test','recruiter')]:
            db().execute('INSERT OR IGNORE INTO users(name,email,password,role) VALUES(?,?,?,?)',(name,email,generate_password_hash((os.environ.get('ADMIN_PASSWORD') or password) if role=='admin' else password),role))
        owner=db().execute("SELECT id FROM users WHERE email='ahmed@example.test'").fetchone()['id']
        if not db().execute('SELECT id FROM jobs LIMIT 1').fetchone():
            for title,loc,contract in [('Ingénieur DevSecOps','Tunis','PFE'),('Analyste SOC','Sousse','CDI'),('Développeur Python','À distance','Stage')]:
                db().execute("INSERT INTO jobs(title,company,location,contract,description,owner,status) VALUES(?,?,?,?,?,?,'active')",(title,'TechNova',loc,contract,'Rejoignez notre équipe pour concevoir des solutions fiables et sécurisées. Compétences : Linux, Git, travail en équipe.',owner))
        db().commit();print('Comptes fictifs et offres créés.')
    return app
