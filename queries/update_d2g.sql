-- :name update_d2g :affected
update details2groups
set count = :count
where group_id = :group_id and exam_nr = :exam_nr