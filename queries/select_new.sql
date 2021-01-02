-- :name get_updated :many
select * from exams where updated datetime(timestamp) >= datetime('now', '-5 Minutes');