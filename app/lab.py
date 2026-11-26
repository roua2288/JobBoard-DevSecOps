"""Four intentionally vulnerable exercises. Loaded only by LAB_MODE=1.
Never publish this mode; use an isolated localhost environment with fake data.
"""
from pathlib import Path
from flask import request, jsonify, abort, g, send_file
def register_lab(app,db,event,require):
    @app.get('/lab/search')
    def lab_search():
        query=request.args.get('q','')[:120]
        rows=db().execute("SELECT title,company FROM jobs WHERE title LIKE '%"+query+"%'").fetchall()
        return jsonify([dict(r) for r in rows])
    @app.get('/lab/preview')
    def lab_preview():
        return '<h1>Aperçu de test</h1>'+request.args.get('text','')
    @app.get('/lab/cv/<int:cv_id>')
    @require()
    def lab_cv(cv_id):
        cv=db().execute('SELECT * FROM cvs WHERE id=?',(cv_id,)).fetchone()
        if not cv:abort(404)
        event('lab_cv_access',cv_id)
        return send_file(Path(app.config['UPLOAD_FOLDER']).resolve()/cv['path'],as_attachment=True,download_name='CV.pdf')
    @app.post('/lab/promote')
    @require()
    def lab_promote():
        # Mass assignment: untrusted role accepted to illustrate privilege escalation.
        role=request.form.get('role','candidate')
        if role not in ('candidate','recruiter','admin'):abort(400)
        db().execute('UPDATE users SET role=? WHERE id=?',(role,g.user['id']));db().commit()
        event('lab_role_changed')
        return jsonify(role=role)
