-- :name get_group :one
select * from groups where name = :name or id = :id