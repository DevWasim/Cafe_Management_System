from app import create_app, db
from app.models import CafeSetting

app = create_app()

with app.app_context():
    setting = CafeSetting.query.first()
    if setting:
        if "Welecome" in setting.hero_title:
            setting.hero_title = setting.hero_title.replace("Welecome", "Welcome")
            db.session.commit()
            print("Fixed typo: Welecome -> Welcome")
        else:
            print("No typo found or already fixed.")
    else:
        print("No settings found.")
