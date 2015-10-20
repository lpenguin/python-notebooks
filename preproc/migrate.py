# -*- coding: utf-8 -*-
#%%
sql_file = '/Users/nikita/Sources/preproc/tmp/preproc.sqlite3'
new_sql_file = '/Users/nikita/Sources/preproc/tmp/preproc-new.sqlite3'

import peewee as pw
import datetime

old_db = pw.SqliteDatabase(sql_file)
new_db = pw.SqliteDatabase(new_sql_file)

class Task(pw.Model):
    name = pw.CharField()
    accession = pw.CharField()
    platform = pw.CharField()
    status = pw.CharField()
    samples = pw.CharField()

    STATUS_EMPTY = 'empty'
    STATUS_SUBMITTED = 'submitted'
    STATUS_PENDING = 'pending'
    STATUS_RUNNING = 'running'
    STATUS_DONE = 'done'
    STATUS_ERROR = 'error'
    
    STATUS_NO_METHOD = 'no-method'
    STATUS_INTERRUPTED = 'interrupted'

    class Meta:
        database = old_db
        

class MetaField(pw.Field):
    db_field = 'text'

    def db_value(self, value):
        return json.dumps(value)

    def python_value(self, value):
        return json.loads(value)


class NewTask(pw.Model):
    STATUS_EMPTY = 'empty'
    STATUS_SUBMITTED = 'submitted'
    STATUS_PENDING = 'pending'
    STATUS_RUNNING = 'running'
    STATUS_DONE = 'done'
    STATUS_ERROR = 'error'

    ERROR_NO_METHOD = 'no-method'
    ERROR_INTERRUPTED = 'interrupted'
    ERROR_NO_DATA = 'no-data'
    ERROR_EXTRACT_ERROR = 'extract-error'
    ERROR_EXECUTION_ERROR = 'exec-error'

    name = pw.CharField()
    status = pw.CharField(default=STATUS_EMPTY)
    meta = MetaField(default={})
    type = pw.CharField()
    error = pw.CharField(null=True)

    creation_date = pw.DateTimeField(null=True, default=datetime.datetime.now)
    submission_date = pw.DateTimeField(null=True)
    run_date = pw.DateTimeField(null=True)
    done_date = pw.DateTimeField(null=True)
    
    class Meta:
        database = new_db

#%%
import json
old_tasks = list(Task.select())

def convert_task(task):
    meta = dict(
        accession=task.accession,
        platform=task.platform,
        samples=task.samples.split(",")
    )
    
    good_statuses = [
        'empty',
        'submitted',
        'pending',
        'running',
        'done',
        'skip'
    ]
    
    if task.status not in good_statuses:
        error = task.status
        task.status = 'error'
    else:
        error = None
    new_task = NewTask(name=task.name,
                       meta=meta,
                       status=task.status,
                       error=error,
                       type='preproc'
                       )    
    return new_task
    
#new_db.create_table(NewTask)

for t in old_tasks:
    convert_task(t).save()

    
    