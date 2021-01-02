-- :name update_exam_details :affected
update exam_details
set average = :average
participants = :participants
where exam_nr = :exam_nr