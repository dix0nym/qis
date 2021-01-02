-- :name update_exam :affected
update exam
set module = :module
part = :part
vs = :vs
note = :note
status = :status
ects = :ects
module_id = :module_id
updated = DateTime('now')
where nr = :nr