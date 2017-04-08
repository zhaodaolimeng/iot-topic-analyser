/**
 * 创建用于文本描述翻译的表
 */
use curiosity_v3;

create table feed_translate_t
select
	t0.feedid, t0.ds_list, t0.tags_list, 
	description, tags, device_name, title, 
	created, lat, lng
from feed_t, (
	select
		feedid,
		group_concat(streamid separator ',') as ds_list,
		group_concat(tags separator ',') as tags_list
	from datastream_t group by feedid
) as t0 where feed_t.id = t0.feedid;

alter table feed_translate_t add column `doc` text after feedid;
alter table feed_translate_t add primary key(feedid);
select * from feed_translate_t;


select feedid, description, ds_list, tags_list from feed_t left join (
	select
		feedid,
		group_concat(streamid separator ',') as ds_list,
		group_concat(tags separator ',') as tags_list
	from datastream_t group by feedid
) as T on feed_t.id = T.feedid;

select  distinct dt.streamid, dt.feedid, dt.tags, dt.current_value, ft.description, ft.device_name 
from datastream_t as dt, feed_t as ft  
where dt.feedid = ft.id;

select 
	feed_t.id, feed_t.description, feed_t.tags, 
	datastream_t.streamid, datastream_t.tags  	
from datastream_t 
left join feed_t on datastream_t.feedid = feed_t.id;


-- 统计描述长度 
select floor(length(description)/100) as desc_length, count(*) as cnt 
from feed_t
where length(description) <> 0
group by floor(length(description)/100)
order by desc_length;

