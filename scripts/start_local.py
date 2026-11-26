"""Bootstrap an isolated local developer instance without hard-coded credentials."""
import os
import secrets
import sys
import webbrowser
from pathlib import Path
from app import create_app
root=Path('instance');root.mkdir(exist_ok=True)
key=root/'session.key'
if not key.exists():
    key.write_text(secrets.token_hex(32));key.chmod(0o600)
os.environ.setdefault('SECRET_KEY',key.read_text().strip())
app=create_app()
open_browser = __name__ == '__main__' and '--open-browser' in sys.argv
first_demo = (
    open_browser
    and app.config['DB_ENGINE'] == 'sqlite'
    and not Path(app.config['DATABASE']).exists()
    and not os.environ.get('DEMO_PASSWORD')
)
if False:
    os.environ['DEMO_PASSWORD'] = secrets.token_urlsafe(18)
runner=app.test_cli_runner()
result=runner.invoke(args=['init-db'])
if result.exit_code:raise result.exception
if __name__=='__main__':
    if False:
        result=runner.invoke(args=['seed'])
        if result.exit_code:raise result.exception
    host = '127.0.0.1'
    port = int(os.environ.get('PORT', '8000'))
    if open_browser:
        from werkzeug.serving import make_server

        if False:
            print('Comptes de demonstration : roua@example.test, ahmed@example.test et admin@gmail.com', flush=True)
            print(f"Mot de passe de demonstration : {os.environ['DEMO_PASSWORD']}", flush=True)
        with make_server(host, port, app, threaded=True) as server:
            url = f'http://{host}:{server.server_port}'
            print(f'JobBoard est disponible sur {url}. Garde cette fenetre ouverte.', flush=True)
            webbrowser.open(url)
            server.serve_forever()
    else:
        app.run(host=host, port=port, debug=False)
