from app import create_app
from app.models import db, Document, DocumentChunk, ChatHistory

app = create_app()

with app.app_context():
    # Delete in correct order due to foreign key constraints
    DocumentChunk.query.delete()
    Document.query.delete()
    ChatHistory.query.delete()  # Optional

    db.session.commit()
    print("🧹 Database cleanup complete!")
