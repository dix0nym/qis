-- :name get_updated :many
select * from exam where datetime(updated) >= datetime('now', :duration);