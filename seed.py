"""
Seed script — Run once to populate stores and create the first admin user.

Usage:
    python seed.py

Make sure your .env (or environment variables) are set before running.
"""
from app import create_app
from app.extensions import db
from app.models.admin import Admin
from app.models.store import Store


def seed():
    app = create_app()
    with app.app_context():
        # --- Stores ---
        stores_data = [
            {'name': 'Shorty Uomo', 'slug': 'uomo'},
            {'name': 'Shorty Woman', 'slug': 'woman'},
            {'name': 'Shorty Intimissimi', 'slug': 'intimissimi'},
        ]

        for s in stores_data:
            existing = Store.query.filter_by(slug=s['slug']).first()
            if not existing:
                store = Store(name=s['name'], slug=s['slug'])
                db.session.add(store)
                print(f"  + Store creato: {s['name']}")
            else:
                print(f"  = Store già esistente: {s['name']}")

        db.session.commit()

        # --- Default Admin ---
        admin_email = 'admin@shortyshop.it'
        existing_admin = Admin.query.filter_by(email=admin_email).first()
        if not existing_admin:
            admin = Admin(
                name='Admin',
                email=admin_email,
                role='superadmin',
            )
            admin.set_password('admin123')  # CHANGE THIS IN PRODUCTION!
            db.session.add(admin)
            db.session.commit()
            print(f"  + Admin creato: {admin_email} / password: admin123")
        else:
            print(f"  = Admin già esistente: {admin_email}")

        print("\nSeed completato!")


if __name__ == '__main__':
    seed()
