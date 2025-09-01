import argparse
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .db import Base, engine as target_engine, SessionLocal
from .models import FlipCard, Tip

def seed_default(session):
    if session.query(FlipCard).count() == 0:
        session.bulk_save_objects([
            FlipCard(id=1, negative_text="I always mess things up.",
                     positive_text="Mistakes are part of learning; try one small step now.", tag="self"),
            FlipCard(id=2, negative_text="I can't finish anything.",
                     positive_text="I can finish one tiny task today.", tag="action"),
            FlipCard(id=3, negative_text="People will judge me.",
                     positive_text="Kind people notice efforts, not perfection.", tag="social"),
            FlipCard(id=4, negative_text="I'm not improving.",
                     positive_text="Progress is uneven; small wins still count.", tag="growth"),
            FlipCard(id=5, negative_text="Everything is my fault.",
                     positive_text="I did my best with what I knew then.", tag="compassion"),
            FlipCard(id=6, negative_text="If I rest, I'm lazy.",
                     positive_text="Rest restores energy so I can come back stronger.", tag="rest"),
            FlipCard(id=7, negative_text="I'm falling behind others.",
                     positive_text="I'm walking my path at my pace.", tag="comparison"),
            FlipCard(id=8, negative_text="I failed again.",
                     positive_text="This is data, not a verdict. Adjust and try again.", tag="learning"),
            FlipCard(id=9, negative_text="I should handle it alone.",
                     positive_text="Asking for help is also strength.", tag="support"),
            FlipCard(id=10, negative_text="It's too late to change.",
                     positive_text="Now is the earliest future I have.", tag="hope"),
        ])
    if session.query(Tip).count() == 0:
        session.bulk_save_objects([
            Tip(id=1, text="Inhale 4s, hold 4s, exhale 6s for one minute.", mood_tag="calm"),
            Tip(id=2, text="Name one thing you did right today.", mood_tag="self-kindness"),
            Tip(id=3, text="Unclench jaw & drop shoulders.", mood_tag="body"),
        ])
    session.commit()
    print("Seeded default data.")

def migrate_from_sqlite(sqlite_path: str):
    src_engine = create_engine(f"sqlite:///{sqlite_path}")
    SrcSession = sessionmaker(bind=src_engine)
    src = SrcSession()
    dst = SessionLocal()

    Base.metadata.create_all(bind=target_engine)

    # FlipCard
    for r in src.query(FlipCard).all():
        if not dst.query(FlipCard).filter_by(id=r.id).first():
            dst.add(FlipCard(id=r.id, negative_text=r.negative_text,
                             positive_text=r.positive_text, tag=r.tag))
    # Tip
    for r in src.query(Tip).all():
        if not dst.query(Tip).filter_by(id=r.id).first():
            dst.add(Tip(id=r.id, text=r.text, mood_tag=r.mood_tag))
    dst.commit()
    print("Migrated data from SQLite → Postgres.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--migrate-from-sqlite", help="path to local SQLite file, e.g. ./app.db")
    args = parser.parse_args()

    Base.metadata.create_all(bind=target_engine)
    if args.migrate_from_sqlite:
        migrate_from_sqlite(args.migrate_from_sqlite)
    else:
        with SessionLocal() as s:
            seed_default(s)
