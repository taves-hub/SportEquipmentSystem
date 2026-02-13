from app import create_app, db
from models import StoreKeeper

def delete_all_storekeepers():
    """Delete all existing storekeepers"""

    app = create_app()
    with app.app_context():
        print("Deleting all existing storekeepers...")
        
        count = StoreKeeper.query.count()
        StoreKeeper.query.delete()
        db.session.commit()
        
        print(f"✅ Deleted {count} storekeepers")

if __name__ == '__main__':
    delete_all_storekeepers()