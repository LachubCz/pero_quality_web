import os
import re
import random
import argparse

import cv2
import numpy as np

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy import func
from app.db import Base, User, Annotation, Crop, Page, Record, Set, RecordCrop


def get_args():
    """
    method for parsing of arguments
    """
    parser = argparse.ArgumentParser()

    parser.add_argument("-t", "--type", choices=["comparing", "ordering", "rating"],
                        required=True, help="type of set")
    parser.add_argument("-n", "--name", required=True, help="name of set")
    parser.add_argument("-d", "--description", default="", help="description of set")
    parser.add_argument("--inactive", action="store_true", help="is set active?")

    parser.add_argument("-f", "--folder", type=str,
                        required=True, help="folder containing crops that are already in database")
    parser.add_argument("-c", "--count", type=int,
                        default=1000, help="Number of records to generate.")
    parser.add_argument("--crop_it", action="store_true", help="save cropped crops?")

    args = parser.parse_args()

    return args


if __name__ == "__main__":
    args = get_args()

    engine = create_engine('sqlite:///database.sqlite3',
                           convert_unicode=True,
                           connect_args={'check_same_thread': False})
    db_session = scoped_session(sessionmaker(autocommit=False,
                                             autoflush=False,
                                             bind=engine))
    Base.query = db_session.query_property()
    Base.metadata.create_all(bind=engine)

    if args.type == "comparing":
        db_set = Set(0, args.name, not args.inactive, args.description)
    elif args.type == "ordering":
        db_set = Set(1, args.name, not args.inactive, args.description)
    elif args.type == "rating":
        db_set = Set(2, args.name, not args.inactive, args.description)

    db_session.add(db_set)
    db_session.commit()
    set_id = db_set.id
    print('Set id', set_id)

    crops_in_record = 1
    if args.type == "comparing":
        crops_in_record = 2
    elif args.type == "ordering":
        crops_in_record = 5

    files = os.listdir(args.folder)
    all_crops = []
    for i, item in enumerate(files):
        all_crops.append(int(item.split(".")[0]))

    print("Writing records")

    if args.type == "rating":
        random.shuffle(all_crops)
        for i, crop in enumerate(all_crops):
            record = Record(i, set_id)
            db_session.add(record)
            db_session.commit()

            record_crop = RecordCrop(crop, record.id, 0)
            db_session.add(record_crop)
            db_session.commit()
    else:
        for i in range(args.count):
            record = Record(i, set_id)
            db_session.add(record)
            db_session.commit()

            selected_crops = np.random.choice(len(all_crops), crops_in_record, replace=False)
            selected_crops = [all_crops[x] for x in selected_crops]
            for order, crop in enumerate(selected_crops):
                record_crop = RecordCrop(crop, record.id, order)
                db_session.add(record_crop)
            db_session.commit()
