import importlib.util
import io
import json
from pathlib import Path


def load_events_server(tmp_path: Path):
    mod_path = Path(__file__).resolve().parents[1] / "events-server.py"
    spec = importlib.util.spec_from_file_location("events_server", mod_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    module.EVENTS_FILE = str(tmp_path / "events.log")
    module.STATE_FILE = str(tmp_path / "state.json")
    module.DB_PATH = str(tmp_path / "auth.db")
    module.UPLOAD_DIR = str(tmp_path / "uploads")
    module.TEMP_TOKENS = {}
    Path(module.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
    Path(module.EVENTS_FILE).touch()

    module.app.config.update(TESTING=True, SECRET_KEY="test-secret")
    with module.app.app_context():
        module.init_db()
    return module


def login(client, username="demo", password="demo-pass"):
    reg = client.post(
        "/register", json={"username": username, "password": password}
    )
    assert reg.status_code == 200
    resp = client.post("/login", json={"username": username, "password": password})
    assert resp.status_code == 200
    assert resp.get_json()["ok"] is True


def test_auth_flow(tmp_path):
    module = load_events_server(tmp_path)
    client = module.app.test_client()

    login(client)
    me = client.get("/me")
    assert me.status_code == 200
    body = me.get_json()
    assert body["ok"] is True
    assert body["username"] == "demo"


def test_upload_files_and_temp_link(tmp_path):
    module = load_events_server(tmp_path)
    client = module.app.test_client()
    login(client, username="uploader", password="pw-12345")

    data = {
        "client_id": "demo-client-1",
        "file": (io.BytesIO(b"hello exhibition"), "hello.txt"),
    }
    upload = client.post("/upload", data=data, content_type="multipart/form-data")
    assert upload.status_code == 200
    assert upload.get_json()["ok"] is True

    files = client.get("/api/files")
    assert files.status_code == 200
    names = [f["name"] for f in files.get_json()["files"]]
    assert "hello.txt" in names

    temp = client.post("/files/temp", json={"name": "hello.txt", "ttl": 300})
    assert temp.status_code == 200
    temp_url = temp.get_json()["url"]

    dl = client.get(temp_url)
    assert dl.status_code == 200
    assert b"hello exhibition" in dl.data


def test_event_log_updates_state(tmp_path):
    module = load_events_server(tmp_path)
    client = module.app.test_client()
    login(client, username="state-user", password="state-pass")

    event = {
        "type": "put_start",
        "detail": {"ip": "client-42", "file": "x.bin", "size": 9},
    }
    resp = client.post("/log_event", json=event)
    assert resp.status_code == 200
    assert resp.get_json()["ok"] is True

    with open(module.EVENTS_FILE, "r") as f:
        last = json.loads(f.readlines()[-1])
    assert last["type"] == "put_start"
    assert last["detail"]["ip"] == "client-42"

    state = client.get("/state")
    assert state.status_code == 200
    nodes = state.get_json()["nodes"]
    assert any(n["ip"] == "client-42" and n["state"] == "transferring" for n in nodes)
