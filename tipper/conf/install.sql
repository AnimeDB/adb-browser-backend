DELIMITER $$

USE {master}$$

DROP FUNCTION IF EXISTS Observed$$

CREATE FUNCTION Observed (mythread INT(10))
RETURNS BOOL
READS SQL DATA
BEGIN
	DECLARE observed INT;
	
	SELECT COUNT(*) INTO observed
		FROM {master}.thread AS t
		NATURAL JOIN {temp}.observed_forums AS o
		WHERE t.threadid = mythread
		GROUP BY o.forumid;
	
	RETURN IFNULL(observed, 0);
END$$


DROP FUNCTION IF EXISTS FirstPost$$

CREATE FUNCTION FirstPost (mypost INT(10), mythread INT(10))
RETURNS BOOL
READS SQL DATA
BEGIN
	DECLARE isfirst INT;
	
	SELECT COUNT(*) INTO isfirst
		FROM {master}.thread AS t
		WHERE t.threadid = mythread AND t.firstpostid = mypost
		GROUP BY t.threadid;
	
	RETURN IFNULL(isfirst, 0);
END$$


DROP TRIGGER IF EXISTS release_inserts$$

CREATE TRIGGER release_inserts AFTER INSERT ON {master}.post
	FOR EACH ROW BEGIN
		IF Observed(NEW.threadid) AND FirstPost(NEW.postid, NEW.threadid) THEN
			INSERT INTO {temp}.post_updates (
				postid, threadid, userid, content, timestamp, action
			) VALUES (
				NEW.postid, NEW.threadid, NEW.userid, NEW.pagetext, UNIX_TIMESTAMP(NOW()), 'inserted'
			);
		END IF;
	END$$


DROP TRIGGER IF EXISTS release_updates$$

CREATE TRIGGER release_updates AFTER UPDATE ON {master}.post
	FOR EACH ROW BEGIN
		IF Observed(NEW.threadid) AND FirstPost(NEW.postid, NEW.threadid) THEN
			INSERT INTO {temp}.post_updates (
				postid, threadid, userid, content, timestamp, action
			) VALUES (
				NEW.postid, NEW.threadid, NEW.userid, NEW.pagetext, UNIX_TIMESTAMP(NOW()), 'updated'
			);
		END IF;
	END$$


DROP TRIGGER IF EXISTS release_deletes$$

CREATE TRIGGER release_deletes AFTER DELETE ON {master}.post
	FOR EACH ROW BEGIN
		IF Observed(OLD.threadid) AND FirstPost(OLD.postid, OLD.threadid) THEN
			INSERT INTO {temp}.post_updates (
				postid, threadid, userid, content, timestamp, action
			) VALUES (
				OLD.postid, OLD.threadid, OLD.userid, OLD.pagetext, UNIX_TIMESTAMP(NOW()), 'deleted'
			);
		END IF;
	END$$

DELIMITER ;

