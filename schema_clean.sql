-- MySQL dump 10.13  Distrib 8.4.3, for Win64 (x86_64)
--
-- Host: localhost    Database: alumni_norsu
-- ------------------------------------------------------
-- Server version	8.4.3

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table account_emailaddress
--

DROP TABLE IF EXISTS account_emailaddress;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE account_emailaddress (
  id int NOT NULL ,
  email varchar(254) NOT NULL,
  verified tinyint(1) NOT NULL,
  primary tinyint(1) NOT NULL,
  user_id int NOT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY account_emailaddress_user_id_email_987c8728_uniq (user_id,email),
  KEY account_emailaddress_upper ((upper(email))),
  CONSTRAINT account_emailaddress_user_id_2c513194_fk_auth_user_id FOREIGN KEY (user_id) REFERENCES auth_user (id)
)   
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table account_emailconfirmation
--

DROP TABLE IF EXISTS account_emailconfirmation;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE account_emailconfirmation (
  id int NOT NULL ,
  created datetime(6) NOT NULL,
  sent datetime(6) DEFAULT NULL,
  key varchar(64) NOT NULL,
  email_address_id int NOT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY key (key),
  KEY account_emailconfirm_email_address_id_5b7f8c58_fk_account_e (email_address_id),
  CONSTRAINT account_emailconfirm_email_address_id_5b7f8c58_fk_account_e FOREIGN KEY (email_address_id) REFERENCES account_emailaddress (id)
)  
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table accounts_document
--

DROP TABLE IF EXISTS accounts_document;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE accounts_document (
  id bigint NOT NULL ,
  title varchar(255) NOT NULL,
  file varchar(100) NOT NULL,
  document_type varchar(20) NOT NULL,
  uploaded_at datetime(6) NOT NULL,
  updated_at datetime(6) NOT NULL,
  is_verified tinyint(1) NOT NULL,
  profile_id bigint NOT NULL,
  PRIMARY KEY (id),
  KEY accounts_document_profile_id_fee23ff2_fk_accounts_profile_id (profile_id),
  CONSTRAINT accounts_document_profile_id_fee23ff2_fk_accounts_profile_id FOREIGN KEY (profile_id) REFERENCES accounts_profile (id)
)  
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table accounts_education
--

DROP TABLE IF EXISTS accounts_education;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE accounts_education (
  id bigint NOT NULL ,
  program varchar(10) DEFAULT NULL,
  major varchar(100) NOT NULL,
  school varchar(10) DEFAULT NULL,
  graduation_year int DEFAULT NULL,
  achievements longtext NOT NULL,
  is_primary tinyint(1) NOT NULL,
  created_at datetime(6) NOT NULL,
  updated_at datetime(6) NOT NULL,
  profile_id bigint NOT NULL,
  PRIMARY KEY (id),
  KEY accounts_education_profile_id_ab3fd502_fk_accounts_profile_id (profile_id),
  CONSTRAINT accounts_education_profile_id_ab3fd502_fk_accounts_profile_id FOREIGN KEY (profile_id) REFERENCES accounts_profile (id)
)   
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table accounts_emailverification
--

DROP TABLE IF EXISTS accounts_emailverification;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE accounts_emailverification (
  id bigint NOT NULL ,
  otp varchar(6) NOT NULL,
  created_at datetime(6) NOT NULL,
  is_verified tinyint(1) NOT NULL,
  expires_at datetime(6) NOT NULL,
  user_id int NOT NULL,
  PRIMARY KEY (id),
  KEY accounts_emailverification_user_id_4f5b1661_fk_auth_user_id (user_id),
  CONSTRAINT accounts_emailverification_user_id_4f5b1661_fk_auth_user_id FOREIGN KEY (user_id) REFERENCES auth_user (id)
)  
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table accounts_experience
--

DROP TABLE IF EXISTS accounts_experience;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE accounts_experience (
  id bigint NOT NULL ,
  company varchar(100) NOT NULL,
  position varchar(100) NOT NULL,
  location varchar(100) NOT NULL,
  start_date date NOT NULL,
  end_date date DEFAULT NULL,
  is_current tinyint(1) NOT NULL,
  description longtext NOT NULL,
  achievements longtext NOT NULL,
  career_significance varchar(20) NOT NULL,
  salary_range varchar(20) NOT NULL,
  skills_gained longtext NOT NULL,
  created_at datetime(6) NOT NULL,
  updated_at datetime(6) NOT NULL,
  profile_id bigint NOT NULL,
  PRIMARY KEY (id),
  KEY accounts_experience_profile_id_91de50a1_fk_accounts_profile_id (profile_id),
  CONSTRAINT accounts_experience_profile_id_91de50a1_fk_accounts_profile_id FOREIGN KEY (profile_id) REFERENCES accounts_profile (id)
)   
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table accounts_mentor
--

DROP TABLE IF EXISTS accounts_mentor;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE accounts_mentor (
  id bigint NOT NULL ,
  expertise_areas longtext NOT NULL,
  availability_status varchar(20) NOT NULL,
  max_mentees int NOT NULL,
  current_mentees int NOT NULL,
  mentoring_experience longtext NOT NULL,
  expectations longtext NOT NULL,
  preferred_contact_method varchar(50) NOT NULL,
  created_at datetime(6) NOT NULL,
  updated_at datetime(6) NOT NULL,
  is_active tinyint(1) NOT NULL,
  is_verified tinyint(1) NOT NULL,
  verification_date datetime(6) DEFAULT NULL,
  accepting_mentees tinyint(1) NOT NULL,
  user_id int NOT NULL,
  verified_by_id int DEFAULT NULL,
  removal_reason longtext,
  removed_at datetime(6) DEFAULT NULL,
  removed_by_id int DEFAULT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY user_id (user_id),
  KEY accounts_mentor_verified_by_id_7addc4e0_fk_auth_user_id (verified_by_id),
  KEY accounts_mentor_removed_by_id_539a9dd8_fk_auth_user_id (removed_by_id),
  CONSTRAINT accounts_mentor_removed_by_id_539a9dd8_fk_auth_user_id FOREIGN KEY (removed_by_id) REFERENCES auth_user (id),
  CONSTRAINT accounts_mentor_user_id_200b98d0_fk_auth_user_id FOREIGN KEY (user_id) REFERENCES auth_user (id),
  CONSTRAINT accounts_mentor_verified_by_id_7addc4e0_fk_auth_user_id FOREIGN KEY (verified_by_id) REFERENCES auth_user (id)
)   
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table accounts_mentorapplication
--

DROP TABLE IF EXISTS accounts_mentorapplication;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE accounts_mentorapplication (
  id bigint NOT NULL ,
  expertise_areas longtext NOT NULL,
  years_of_experience int NOT NULL,
  certifications varchar(100) NOT NULL,
  training_documents varchar(100) NOT NULL,
  competency_summary longtext NOT NULL,
  application_date datetime(6) NOT NULL,
  review_date datetime(6) DEFAULT NULL,
  status varchar(20) NOT NULL,
  review_notes longtext NOT NULL,
  reviewed_by_id int DEFAULT NULL,
  user_id int NOT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY user_id (user_id),
  KEY accounts_mentorappli_reviewed_by_id_f94e838f_fk_auth_user (reviewed_by_id),
  CONSTRAINT accounts_mentorappli_reviewed_by_id_f94e838f_fk_auth_user FOREIGN KEY (reviewed_by_id) REFERENCES auth_user (id),
  CONSTRAINT accounts_mentorapplication_user_id_5eb470ed_fk_auth_user_id FOREIGN KEY (user_id) REFERENCES auth_user (id)
)   
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table accounts_mentorreactivationrequest
--

DROP TABLE IF EXISTS accounts_mentorreactivationrequest;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE accounts_mentorreactivationrequest (
  id bigint NOT NULL ,
  email varchar(254) NOT NULL,
  verification_code varchar(6) NOT NULL,
  is_verified tinyint(1) NOT NULL,
  status varchar(20) NOT NULL,
  request_reason longtext NOT NULL,
  admin_notes longtext NOT NULL,
  requested_at datetime(6) NOT NULL,
  reviewed_at datetime(6) DEFAULT NULL,
  verification_code_expires_at datetime(6) DEFAULT NULL,
  mentor_id bigint NOT NULL,
  requested_by_id int NOT NULL,
  reviewed_by_id int DEFAULT NULL,
  PRIMARY KEY (id),
  KEY accounts_mentorreact_mentor_id_971e311c_fk_accounts_ (mentor_id),
  KEY accounts_mentorreact_requested_by_id_365af7dc_fk_auth_user (requested_by_id),
  KEY accounts_mentorreact_reviewed_by_id_49f30421_fk_auth_user (reviewed_by_id),
  CONSTRAINT accounts_mentorreact_mentor_id_971e311c_fk_accounts_ FOREIGN KEY (mentor_id) REFERENCES accounts_mentor (id),
  CONSTRAINT accounts_mentorreact_requested_by_id_365af7dc_fk_auth_user FOREIGN KEY (requested_by_id) REFERENCES auth_user (id),
  CONSTRAINT accounts_mentorreact_reviewed_by_id_49f30421_fk_auth_user FOREIGN KEY (reviewed_by_id) REFERENCES auth_user (id)
)  
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table accounts_mentorshiprequest
--

DROP TABLE IF EXISTS accounts_mentorshiprequest;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE accounts_mentorshiprequest (
  id bigint NOT NULL ,
  skills_seeking longtext NOT NULL,
  goals longtext NOT NULL,
  message longtext NOT NULL,
  status varchar(20) NOT NULL,
  start_date date DEFAULT NULL,
  end_date date DEFAULT NULL,
  expected_end_date date DEFAULT NULL,
  timeline_milestones longtext NOT NULL,
  progress_percentage int NOT NULL,
  created_at datetime(6) NOT NULL,
  updated_at datetime(6) NOT NULL,
  feedback longtext NOT NULL,
  rating int DEFAULT NULL,
  mentee_id int NOT NULL,
  mentor_id bigint NOT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY accounts_mentorshipreque_mentor_id_mentee_id_stat_1300596c_uniq (mentor_id,mentee_id,status),
  KEY accounts_mentorshiprequest_mentee_id_c6695197_fk_auth_user_id (mentee_id),
  CONSTRAINT accounts_mentorshipr_mentor_id_0d065274_fk_accounts_ FOREIGN KEY (mentor_id) REFERENCES accounts_mentor (id),
  CONSTRAINT accounts_mentorshiprequest_mentee_id_c6695197_fk_auth_user_id FOREIGN KEY (mentee_id) REFERENCES auth_user (id)
)  
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table accounts_profile
--

DROP TABLE IF EXISTS accounts_profile;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE accounts_profile (
  id bigint NOT NULL ,
  avatar varchar(100) DEFAULT NULL,
  bio longtext NOT NULL,
  birth_date date DEFAULT NULL,
  gender varchar(1) NOT NULL,
  current_position varchar(200) NOT NULL,
  current_employer varchar(200) NOT NULL,
  industry varchar(200) NOT NULL,
  employment_status varchar(20) NOT NULL,
  salary_range varchar(20) NOT NULL,
  phone_number varchar(128) NOT NULL,
  address varchar(255) NOT NULL,
  city varchar(100) NOT NULL,
  state varchar(100) NOT NULL,
  country varchar(2) NOT NULL,
  postal_code varchar(20) NOT NULL,
  linkedin_profile varchar(255) NOT NULL,
  facebook_profile varchar(255) NOT NULL,
  twitter_profile varchar(255) NOT NULL,
  is_public tinyint(1) NOT NULL,
  created_at datetime(6) NOT NULL,
  updated_at datetime(6) NOT NULL,
  has_completed_registration tinyint(1) NOT NULL,
  user_id int NOT NULL,
  is_hr tinyint(1) NOT NULL,
  is_alumni_coordinator tinyint(1) NOT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY user_id (user_id),
  CONSTRAINT accounts_profile_user_id_49a85d32_fk_auth_user_id FOREIGN KEY (user_id) REFERENCES auth_user (id)
)   
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table accounts_skill
--

DROP TABLE IF EXISTS accounts_skill;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE accounts_skill (
  id bigint NOT NULL ,
  name varchar(100) NOT NULL,
  skill_type varchar(10) NOT NULL,
  proficiency_level int NOT NULL,
  years_of_experience int NOT NULL,
  last_used date DEFAULT NULL,
  is_primary tinyint(1) NOT NULL,
  created_at datetime(6) NOT NULL,
  updated_at datetime(6) NOT NULL,
  profile_id bigint NOT NULL,
  PRIMARY KEY (id),
  KEY accounts_skill_profile_id_55a19265_fk_accounts_profile_id (profile_id),
  KEY accounts_sk_name_a2ce97_idx (name,skill_type),
  KEY accounts_sk_profici_917885_idx (proficiency_level),
  CONSTRAINT accounts_skill_profile_id_55a19265_fk_accounts_profile_id FOREIGN KEY (profile_id) REFERENCES accounts_profile (id)
)  
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table accounts_skillmatch
--

DROP TABLE IF EXISTS accounts_skillmatch;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE accounts_skillmatch (
  id bigint NOT NULL ,
  match_score double NOT NULL,
  matched_skills longtext NOT NULL,
  missing_skills longtext NOT NULL,
  created_at datetime(6) NOT NULL,
  is_notified tinyint(1) NOT NULL,
  is_viewed tinyint(1) NOT NULL,
  is_applied tinyint(1) NOT NULL,
  job_id bigint NOT NULL,
  profile_id bigint NOT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY accounts_skillmatch_job_id_profile_id_9fb24ecd_uniq (job_id,profile_id),
  KEY accounts_skillmatch_profile_id_76d7bd5b_fk_accounts_profile_id (profile_id),
  KEY accounts_sk_match_s_d68ee8_idx (match_score),
  KEY accounts_sk_created_18c0cb_idx (created_at),
  CONSTRAINT accounts_skillmatch_job_id_94a731a5_fk_jobs_jobposting_id FOREIGN KEY (job_id) REFERENCES jobs_jobposting (id),
  CONSTRAINT accounts_skillmatch_profile_id_76d7bd5b_fk_accounts_profile_id FOREIGN KEY (profile_id) REFERENCES accounts_profile (id)
)  
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table alumni_directory_achievement
--

DROP TABLE IF EXISTS alumni_directory_achievement;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE alumni_directory_achievement (
  id bigint NOT NULL ,
  title varchar(255) NOT NULL,
  achievement_type varchar(20) NOT NULL,
  date_achieved date NOT NULL,
  description longtext NOT NULL,
  issuer varchar(255) NOT NULL,
  url varchar(200) NOT NULL,
  attachment varchar(100) DEFAULT NULL,
  created_at datetime(6) NOT NULL,
  updated_at datetime(6) NOT NULL,
  alumni_id bigint NOT NULL,
  PRIMARY KEY (id),
  KEY alumni_directory_ach_alumni_id_81a657d8_fk_alumni_di (alumni_id),
  CONSTRAINT alumni_directory_ach_alumni_id_81a657d8_fk_alumni_di FOREIGN KEY (alumni_id) REFERENCES alumni_directory_alumni (id)
)  
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table alumni_directory_alumni
--

DROP TABLE IF EXISTS alumni_directory_alumni;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE alumni_directory_alumni (
  id bigint NOT NULL ,
  college varchar(10) NOT NULL,
  campus varchar(10) NOT NULL,
  graduation_year int NOT NULL,
  course varchar(200) NOT NULL,
  major varchar(200) NOT NULL,
  honors varchar(200) NOT NULL,
  thesis_title varchar(500) DEFAULT NULL,
  gender varchar(1) NOT NULL,
  date_of_birth date DEFAULT NULL,
  phone_number varchar(128) NOT NULL,
  alternate_email varchar(254) NOT NULL,
  linkedin_profile varchar(200) NOT NULL,
  country varchar(2) NOT NULL,
  province varchar(100) NOT NULL,
  city varchar(100) NOT NULL,
  address longtext NOT NULL,
  current_company varchar(200) NOT NULL,
  job_title varchar(200) NOT NULL,
  employment_status varchar(20) NOT NULL,
  industry varchar(200) NOT NULL,
  skills longtext NOT NULL,
  interests longtext NOT NULL,
  bio longtext NOT NULL,
  achievements longtext NOT NULL,
  created_at datetime(6) NOT NULL,
  updated_at datetime(6) NOT NULL,
  is_verified tinyint(1) NOT NULL,
  is_featured tinyint(1) NOT NULL,
  mentorship_status varchar(20) NOT NULL,
  user_id int NOT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY user_id (user_id),
  KEY alumni_dire_graduat_d32c0e_idx (graduation_year,course),
  KEY alumni_dire_provinc_1f8edb_idx (province,city),
  KEY alumni_dire_college_b08d1c_idx (college,campus),
  KEY alumni_dire_mentors_d7abb9_idx (mentorship_status),
  CONSTRAINT alumni_directory_alumni_user_id_ad41c6f0_fk_auth_user_id FOREIGN KEY (user_id) REFERENCES auth_user (id)
)   
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table alumni_directory_alumnidocument
--

DROP TABLE IF EXISTS alumni_directory_alumnidocument;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE alumni_directory_alumnidocument (
  id bigint NOT NULL ,
  title varchar(255) NOT NULL,
  document_type varchar(20) NOT NULL,
  file varchar(100) NOT NULL,
  description longtext NOT NULL,
  uploaded_at datetime(6) NOT NULL,
  is_verified tinyint(1) NOT NULL,
  alumni_id bigint NOT NULL,
  PRIMARY KEY (id),
  KEY alumni_directory_alu_alumni_id_1aaf2faa_fk_alumni_di (alumni_id),
  CONSTRAINT alumni_directory_alu_alumni_id_1aaf2faa_fk_alumni_di FOREIGN KEY (alumni_id) REFERENCES alumni_directory_alumni (id)
)  
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table alumni_groups_alumnigroup
--

DROP TABLE IF EXISTS alumni_groups_alumnigroup;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE alumni_groups_alumnigroup (
  id bigint NOT NULL ,
  name varchar(255) NOT NULL,
  slug varchar(255) NOT NULL,
  description longtext NOT NULL,
  group_type varchar(10) NOT NULL,
  visibility varchar(10) NOT NULL,
  batch_start_year int DEFAULT NULL,
  batch_end_year int DEFAULT NULL,
  course varchar(100) NOT NULL,
  campus varchar(20) NOT NULL,
  created_at datetime(6) NOT NULL,
  updated_at datetime(6) NOT NULL,
  is_active tinyint(1) NOT NULL,
  requires_approval tinyint(1) NOT NULL,
  has_security_questions tinyint(1) NOT NULL,
  require_post_approval tinyint(1) NOT NULL,
  max_members int DEFAULT NULL,
  cover_image varchar(100) DEFAULT NULL,
  created_by_id int DEFAULT NULL,
  profile_photo varchar(100) DEFAULT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY slug (slug),
  KEY alumni_grou_name_7eca69_idx (name,group_type,visibility),
  KEY alumni_grou_batch_s_c8736c_idx (batch_start_year,batch_end_year),
  KEY alumni_grou_course_be91eb_idx (course,campus),
  KEY alumni_groups_alumnigroup_created_by_id_dff59be4_fk_auth_user_id (created_by_id),
  CONSTRAINT alumni_groups_alumnigroup_created_by_id_dff59be4_fk_auth_user_id FOREIGN KEY (created_by_id) REFERENCES auth_user (id)
)   
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table alumni_groups_comment
--

DROP TABLE IF EXISTS alumni_groups_comment;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE alumni_groups_comment (
  id bigint NOT NULL ,
  content longtext NOT NULL,
  created_at datetime(6) NOT NULL,
  updated_at datetime(6) NOT NULL,
  author_id int NOT NULL,
  post_id bigint NOT NULL,
  PRIMARY KEY (id),
  KEY alumni_groups_comment_author_id_35f057f3_fk_auth_user_id (author_id),
  KEY alumni_groups_comment_post_id_94271a96_fk_alumni_groups_post_id (post_id),
  CONSTRAINT alumni_groups_comment_author_id_35f057f3_fk_auth_user_id FOREIGN KEY (author_id) REFERENCES auth_user (id),
  CONSTRAINT alumni_groups_comment_post_id_94271a96_fk_alumni_groups_post_id FOREIGN KEY (post_id) REFERENCES alumni_groups_post (id)
)  
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table alumni_groups_groupactivity
--

DROP TABLE IF EXISTS alumni_groups_groupactivity;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE alumni_groups_groupactivity (
  id bigint NOT NULL ,
  activity_type varchar(10) NOT NULL,
  description longtext NOT NULL,
  created_at datetime(6) NOT NULL,
  group_id bigint NOT NULL,
  user_id int NOT NULL,
  PRIMARY KEY (id),
  KEY alumni_groups_groupa_group_id_e80dafca_fk_alumni_gr (group_id),
  KEY alumni_groups_groupactivity_user_id_c53f23f7_fk_auth_user_id (user_id),
  CONSTRAINT alumni_groups_groupa_group_id_e80dafca_fk_alumni_gr FOREIGN KEY (group_id) REFERENCES alumni_groups_alumnigroup (id),
  CONSTRAINT alumni_groups_groupactivity_user_id_c53f23f7_fk_auth_user_id FOREIGN KEY (user_id) REFERENCES auth_user (id)
)   
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table alumni_groups_groupanalytics
--

DROP TABLE IF EXISTS alumni_groups_groupanalytics;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE alumni_groups_groupanalytics (
  id bigint NOT NULL ,
  total_members int unsigned NOT NULL,
  active_members int unsigned NOT NULL,
  total_posts int unsigned NOT NULL,
  total_events int unsigned NOT NULL,
  total_comments int unsigned NOT NULL,
  engagement_rate double NOT NULL,
  last_updated datetime(6) NOT NULL,
  group_id bigint NOT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY group_id (group_id),
  CONSTRAINT alumni_groups_groupa_group_id_cb8802d6_fk_alumni_gr FOREIGN KEY (group_id) REFERENCES alumni_groups_alumnigroup (id),
  CONSTRAINT alumni_groups_groupanalytics_chk_1 CHECK ((total_members >= 0)),
  CONSTRAINT alumni_groups_groupanalytics_chk_2 CHECK ((active_members >= 0)),
  CONSTRAINT alumni_groups_groupanalytics_chk_3 CHECK ((total_posts >= 0)),
  CONSTRAINT alumni_groups_groupanalytics_chk_4 CHECK ((total_events >= 0)),
  CONSTRAINT alumni_groups_groupanalytics_chk_5 CHECK ((total_comments >= 0))
)   
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table alumni_groups_groupdiscussion
--

DROP TABLE IF EXISTS alumni_groups_groupdiscussion;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE alumni_groups_groupdiscussion (
  id bigint NOT NULL ,
  title varchar(255) NOT NULL,
  content longtext NOT NULL,
  created_at datetime(6) NOT NULL,
  updated_at datetime(6) NOT NULL,
  is_pinned tinyint(1) NOT NULL,
  is_locked tinyint(1) NOT NULL,
  views_count int unsigned NOT NULL,
  created_by_id int NOT NULL,
  group_id bigint NOT NULL,
  PRIMARY KEY (id),
  KEY alumni_groups_groupd_created_by_id_927bd6df_fk_auth_user (created_by_id),
  KEY alumni_groups_groupd_group_id_6335aee9_fk_alumni_gr (group_id),
  CONSTRAINT alumni_groups_groupd_created_by_id_927bd6df_fk_auth_user FOREIGN KEY (created_by_id) REFERENCES auth_user (id),
  CONSTRAINT alumni_groups_groupd_group_id_6335aee9_fk_alumni_gr FOREIGN KEY (group_id) REFERENCES alumni_groups_alumnigroup (id),
  CONSTRAINT alumni_groups_groupdiscussion_chk_1 CHECK ((views_count >= 0))
)  
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table alumni_groups_groupdiscussioncomment
--

DROP TABLE IF EXISTS alumni_groups_groupdiscussioncomment;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE alumni_groups_groupdiscussioncomment (
  id bigint NOT NULL ,
  content longtext NOT NULL,
  created_at datetime(6) NOT NULL,
  updated_at datetime(6) NOT NULL,
  created_by_id int NOT NULL,
  discussion_id bigint NOT NULL,
  parent_id bigint DEFAULT NULL,
  PRIMARY KEY (id),
  KEY alumni_groups_groupd_created_by_id_dd8e80fc_fk_auth_user (created_by_id),
  KEY alumni_groups_groupd_discussion_id_66ee8eb1_fk_alumni_gr (discussion_id),
  KEY alumni_groups_groupd_parent_id_f6e1810c_fk_alumni_gr (parent_id),
  CONSTRAINT alumni_groups_groupd_created_by_id_dd8e80fc_fk_auth_user FOREIGN KEY (created_by_id) REFERENCES auth_user (id),
  CONSTRAINT alumni_groups_groupd_discussion_id_66ee8eb1_fk_alumni_gr FOREIGN KEY (discussion_id) REFERENCES alumni_groups_groupdiscussion (id),
  CONSTRAINT alumni_groups_groupd_parent_id_f6e1810c_fk_alumni_gr FOREIGN KEY (parent_id) REFERENCES alumni_groups_groupdiscussioncomment (id)
)  
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table alumni_groups_groupevent
--

DROP TABLE IF EXISTS alumni_groups_groupevent;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE alumni_groups_groupevent (
  id bigint NOT NULL ,
  title varchar(255) NOT NULL,
  description longtext NOT NULL,
  start_date datetime(6) NOT NULL,
  end_date datetime(6) NOT NULL,
  latitude decimal(9,6) DEFAULT NULL,
  longitude decimal(9,6) DEFAULT NULL,
  address varchar(255) NOT NULL,
  is_online tinyint(1) NOT NULL,
  meeting_link varchar(200) NOT NULL,
  created_at datetime(6) NOT NULL,
  updated_at datetime(6) NOT NULL,
  max_participants int DEFAULT NULL,
  is_active tinyint(1) NOT NULL,
  created_by_id int DEFAULT NULL,
  group_id bigint NOT NULL,
  PRIMARY KEY (id),
  KEY alumni_groups_groupevent_created_by_id_1fe6d883_fk_auth_user_id (created_by_id),
  KEY alumni_groups_groupe_group_id_7926354e_fk_alumni_gr (group_id),
  CONSTRAINT alumni_groups_groupe_group_id_7926354e_fk_alumni_gr FOREIGN KEY (group_id) REFERENCES alumni_groups_alumnigroup (id),
  CONSTRAINT alumni_groups_groupevent_created_by_id_1fe6d883_fk_auth_user_id FOREIGN KEY (created_by_id) REFERENCES auth_user (id)
)  
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table alumni_groups_groupfile
--

DROP TABLE IF EXISTS alumni_groups_groupfile;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE alumni_groups_groupfile (
  id bigint NOT NULL ,
  title varchar(255) NOT NULL,
  file varchar(100) NOT NULL,
  uploaded_at datetime(6) NOT NULL,
  description longtext NOT NULL,
  download_count int unsigned NOT NULL,
  group_id bigint NOT NULL,
  uploaded_by_id int NOT NULL,
  PRIMARY KEY (id),
  KEY alumni_groups_groupf_group_id_104a8c09_fk_alumni_gr (group_id),
  KEY alumni_groups_groupfile_uploaded_by_id_7c7faf6b_fk_auth_user_id (uploaded_by_id),
  CONSTRAINT alumni_groups_groupf_group_id_104a8c09_fk_alumni_gr FOREIGN KEY (group_id) REFERENCES alumni_groups_alumnigroup (id),
  CONSTRAINT alumni_groups_groupfile_uploaded_by_id_7c7faf6b_fk_auth_user_id FOREIGN KEY (uploaded_by_id) REFERENCES auth_user (id),
  CONSTRAINT alumni_groups_groupfile_chk_1 CHECK ((download_count >= 0))
)  
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table alumni_groups_groupmembership
--

DROP TABLE IF EXISTS alumni_groups_groupmembership;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE alumni_groups_groupmembership (
  id bigint NOT NULL ,
  role varchar(10) NOT NULL,
  status varchar(10) NOT NULL,
  joined_at datetime(6) NOT NULL,
  is_active tinyint(1) NOT NULL,
  last_active_at datetime(6) NOT NULL,
  group_id bigint NOT NULL,
  user_id int NOT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY alumni_groups_groupmembership_group_id_user_id_04ae29b3_uniq (group_id,user_id),
  KEY alumni_grou_group_i_10f212_idx (group_id,user_id,role,status),
  KEY alumni_groups_groupmembership_user_id_10488d04_fk_auth_user_id (user_id),
  CONSTRAINT alumni_groups_groupm_group_id_52376ed0_fk_alumni_gr FOREIGN KEY (group_id) REFERENCES alumni_groups_alumnigroup (id),
  CONSTRAINT alumni_groups_groupmembership_user_id_10488d04_fk_auth_user_id FOREIGN KEY (user_id) REFERENCES auth_user (id)
)   
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table alumni_groups_groupmessage
--

DROP TABLE IF EXISTS alumni_groups_groupmessage;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE alumni_groups_groupmessage (
  id bigint NOT NULL ,
  content longtext NOT NULL,
  created_at datetime(6) NOT NULL,
  group_id bigint NOT NULL,
  user_id int NOT NULL,
  PRIMARY KEY (id),
  KEY alumni_groups_groupm_group_id_eeb52cc6_fk_alumni_gr (group_id),
  KEY alumni_groups_groupmessage_user_id_f9988406_fk_auth_user_id (user_id),
  CONSTRAINT alumni_groups_groupm_group_id_eeb52cc6_fk_alumni_gr FOREIGN KEY (group_id) REFERENCES alumni_groups_alumnigroup (id),
  CONSTRAINT alumni_groups_groupmessage_user_id_f9988406_fk_auth_user_id FOREIGN KEY (user_id) REFERENCES auth_user (id)
)   
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table alumni_groups_post
--

DROP TABLE IF EXISTS alumni_groups_post;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE alumni_groups_post (
  id bigint NOT NULL ,
  content longtext NOT NULL,
  created_at datetime(6) NOT NULL,
  updated_at datetime(6) NOT NULL,
  status varchar(10) NOT NULL,
  approved_at datetime(6) DEFAULT NULL,
  approved_by_id int DEFAULT NULL,
  author_id int NOT NULL,
  group_id bigint NOT NULL,
  PRIMARY KEY (id),
  KEY alumni_groups_post_approved_by_id_de036856_fk_auth_user_id (approved_by_id),
  KEY alumni_groups_post_author_id_c4e4c2c1_fk_auth_user_id (author_id),
  KEY alumni_groups_post_group_id_f3277e3c_fk_alumni_gr (group_id),
  CONSTRAINT alumni_groups_post_approved_by_id_de036856_fk_auth_user_id FOREIGN KEY (approved_by_id) REFERENCES auth_user (id),
  CONSTRAINT alumni_groups_post_author_id_c4e4c2c1_fk_auth_user_id FOREIGN KEY (author_id) REFERENCES auth_user (id),
  CONSTRAINT alumni_groups_post_group_id_f3277e3c_fk_alumni_gr FOREIGN KEY (group_id) REFERENCES alumni_groups_alumnigroup (id)
)  
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table alumni_groups_postlike
--

DROP TABLE IF EXISTS alumni_groups_postlike;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE alumni_groups_postlike (
  id bigint NOT NULL ,
  created_at datetime(6) NOT NULL,
  post_id bigint NOT NULL,
  user_id int NOT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY alumni_groups_postlike_post_id_user_id_7bd30ce6_uniq (post_id,user_id),
  KEY alumni_groups_postlike_user_id_cc1e40ff_fk_auth_user_id (user_id),
  CONSTRAINT alumni_groups_postlike_post_id_e31c4126_fk_alumni_groups_post_id FOREIGN KEY (post_id) REFERENCES alumni_groups_post (id),
  CONSTRAINT alumni_groups_postlike_user_id_cc1e40ff_fk_auth_user_id FOREIGN KEY (user_id) REFERENCES auth_user (id)
)  
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table alumni_groups_securityquestion
--

DROP TABLE IF EXISTS alumni_groups_securityquestion;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE alumni_groups_securityquestion (
  id bigint NOT NULL ,
  question varchar(255) NOT NULL,
  is_required tinyint(1) NOT NULL,
  created_at datetime(6) NOT NULL,
  updated_at datetime(6) NOT NULL,
  group_id bigint NOT NULL,
  PRIMARY KEY (id),
  KEY alumni_groups_securi_group_id_cc6766b9_fk_alumni_gr (group_id),
  CONSTRAINT alumni_groups_securi_group_id_cc6766b9_fk_alumni_gr FOREIGN KEY (group_id) REFERENCES alumni_groups_alumnigroup (id)
)  
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table alumni_groups_securityquestionanswer
--

DROP TABLE IF EXISTS alumni_groups_securityquestionanswer;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE alumni_groups_securityquestionanswer (
  id bigint NOT NULL ,
  answer longtext NOT NULL,
  created_at datetime(6) NOT NULL,
  is_correct tinyint(1) DEFAULT NULL,
  reviewed_at datetime(6) DEFAULT NULL,
  membership_id bigint NOT NULL,
  question_id bigint NOT NULL,
  reviewed_by_id int DEFAULT NULL,
  PRIMARY KEY (id),
  KEY alumni_groups_securi_membership_id_0d1d15e8_fk_alumni_gr (membership_id),
  KEY alumni_groups_securi_question_id_9dfd4e9c_fk_alumni_gr (question_id),
  KEY alumni_groups_securi_reviewed_by_id_4e859cdb_fk_auth_user (reviewed_by_id),
  CONSTRAINT alumni_groups_securi_membership_id_0d1d15e8_fk_alumni_gr FOREIGN KEY (membership_id) REFERENCES alumni_groups_groupmembership (id),
  CONSTRAINT alumni_groups_securi_question_id_9dfd4e9c_fk_alumni_gr FOREIGN KEY (question_id) REFERENCES alumni_groups_securityquestion (id),
  CONSTRAINT alumni_groups_securi_reviewed_by_id_4e859cdb_fk_auth_user FOREIGN KEY (reviewed_by_id) REFERENCES auth_user (id)
)  
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table announcements_announcement
--

DROP TABLE IF EXISTS announcements_announcement;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE announcements_announcement (
  id bigint NOT NULL ,
  title varchar(200) NOT NULL,
  content longtext NOT NULL,
  date_posted datetime(6) NOT NULL,
  last_modified datetime(6) NOT NULL,
  priority_level varchar(10) NOT NULL,
  target_audience varchar(20) NOT NULL,
  is_active tinyint(1) NOT NULL,
  views_count int unsigned NOT NULL,
  category_id bigint DEFAULT NULL,
  PRIMARY KEY (id),
  KEY announcemen_date_po_53d3b6_idx (date_posted DESC),
  KEY announcemen_categor_50d4b6_idx (category_id,date_posted DESC),
  CONSTRAINT announcements_announ_category_id_81df114b_fk_announcem FOREIGN KEY (category_id) REFERENCES announcements_category (id),
  CONSTRAINT announcements_announcement_chk_1 CHECK ((views_count >= 0))
)   
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table announcements_category
--

DROP TABLE IF EXISTS announcements_category;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE announcements_category (
  id bigint NOT NULL ,
  name varchar(100) NOT NULL,
  description longtext NOT NULL,
  slug varchar(50) NOT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY slug (slug)
)   
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table auth_group
--

DROP TABLE IF EXISTS auth_group;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE auth_group (
  id int NOT NULL ,
  name varchar(150) NOT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY name (name)
)  
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table auth_group_permissions
--

DROP TABLE IF EXISTS auth_group_permissions;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE auth_group_permissions (
  id bigint NOT NULL ,
  group_id int NOT NULL,
  permission_id int NOT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY auth_group_permissions_group_id_permission_id_0cd325b0_uniq (group_id,permission_id),
  KEY auth_group_permissio_permission_id_84c5c92e_fk_auth_perm (permission_id),
  CONSTRAINT auth_group_permissio_permission_id_84c5c92e_fk_auth_perm FOREIGN KEY (permission_id) REFERENCES auth_permission (id),
  CONSTRAINT auth_group_permissions_group_id_b120cbf9_fk_auth_group_id FOREIGN KEY (group_id) REFERENCES auth_group (id)
)  
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table auth_permission
--

DROP TABLE IF EXISTS auth_permission;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE auth_permission (
  id int NOT NULL ,
  name varchar(255) NOT NULL,
  content_type_id int NOT NULL,
  codename varchar(100) NOT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY auth_permission_content_type_id_codename_01ab375a_uniq (content_type_id,codename),
  CONSTRAINT auth_permission_content_type_id_2f476e4b_fk_django_co FOREIGN KEY (content_type_id) REFERENCES django_content_type (id)
)   
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table auth_user
--

DROP TABLE IF EXISTS auth_user;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE auth_user (
  id int NOT NULL ,
  password varchar(128) NOT NULL,
  last_login datetime(6) DEFAULT NULL,
  is_superuser tinyint(1) NOT NULL,
  username varchar(150) NOT NULL,
  first_name varchar(150) NOT NULL,
  last_name varchar(150) NOT NULL,
  email varchar(254) NOT NULL,
  is_staff tinyint(1) NOT NULL,
  is_active tinyint(1) NOT NULL,
  date_joined datetime(6) NOT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY username (username)
)   
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table auth_user_groups
--

DROP TABLE IF EXISTS auth_user_groups;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE auth_user_groups (
  id bigint NOT NULL ,
  user_id int NOT NULL,
  group_id int NOT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY auth_user_groups_user_id_group_id_94350c0c_uniq (user_id,group_id),
  KEY auth_user_groups_group_id_97559544_fk_auth_group_id (group_id),
  CONSTRAINT auth_user_groups_group_id_97559544_fk_auth_group_id FOREIGN KEY (group_id) REFERENCES auth_group (id),
  CONSTRAINT auth_user_groups_user_id_6a12ed8b_fk_auth_user_id FOREIGN KEY (user_id) REFERENCES auth_user (id)
)  
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table auth_user_user_permissions
--

DROP TABLE IF EXISTS auth_user_user_permissions;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE auth_user_user_permissions (
  id bigint NOT NULL ,
  user_id int NOT NULL,
  permission_id int NOT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY auth_user_user_permissions_user_id_permission_id_14a6b632_uniq (user_id,permission_id),
  KEY auth_user_user_permi_permission_id_1fbb5f2c_fk_auth_perm (permission_id),
  CONSTRAINT auth_user_user_permi_permission_id_1fbb5f2c_fk_auth_perm FOREIGN KEY (permission_id) REFERENCES auth_permission (id),
  CONSTRAINT auth_user_user_permissions_user_id_a95ead1b_fk_auth_user_id FOREIGN KEY (user_id) REFERENCES auth_user (id)
)  
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table cms_alumnistatistic
--

DROP TABLE IF EXISTS cms_alumnistatistic;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE cms_alumnistatistic (
  id bigint NOT NULL ,
  created datetime(6) NOT NULL,
  modified datetime(6) NOT NULL,
  statistic_type varchar(30) NOT NULL,
  value varchar(20) NOT NULL,
  label varchar(100) NOT NULL,
  icon varchar(50) NOT NULL,
  icon_color varchar(7) NOT NULL,
  order int unsigned NOT NULL,
  is_active tinyint(1) NOT NULL,
  PRIMARY KEY (id),
  CONSTRAINT cms_alumnistatistic_chk_1 CHECK ((order >= 0))
)   
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table cms_contactinfo
--

DROP TABLE IF EXISTS cms_contactinfo;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE cms_contactinfo (
  id bigint NOT NULL ,
  created datetime(6) NOT NULL,
  modified datetime(6) NOT NULL,
  contact_type varchar(20) NOT NULL,
  value longtext NOT NULL,
  is_primary tinyint(1) NOT NULL,
  order int unsigned NOT NULL,
  is_active tinyint(1) NOT NULL,
  PRIMARY KEY (id),
  CONSTRAINT cms_contactinfo_chk_1 CHECK ((order >= 0))
)   
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table cms_faq
--

DROP TABLE IF EXISTS cms_faq;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE cms_faq (
  id bigint NOT NULL ,
  created datetime(6) NOT NULL,
  modified datetime(6) NOT NULL,
  question varchar(500) NOT NULL,
  answer longtext NOT NULL,
  order int unsigned NOT NULL,
  is_active tinyint(1) NOT NULL,
  PRIMARY KEY (id),
  CONSTRAINT cms_faq_chk_1 CHECK ((order >= 0))
)   
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table cms_feature
--

DROP TABLE IF EXISTS cms_feature;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE cms_feature (
  id bigint NOT NULL ,
  created datetime(6) NOT NULL,
  modified datetime(6) NOT NULL,
  title varchar(200) NOT NULL,
  content longtext NOT NULL,
  icon varchar(50) NOT NULL,
  icon_class varchar(50) NOT NULL,
  link_url varchar(200) NOT NULL,
  link_text varchar(100) NOT NULL,
  order int unsigned NOT NULL,
  is_active tinyint(1) NOT NULL,
  PRIMARY KEY (id),
  CONSTRAINT cms_feature_chk_1 CHECK ((order >= 0))
)   
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table cms_footerlink
--

DROP TABLE IF EXISTS cms_footerlink;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE cms_footerlink (
  id bigint NOT NULL ,
  created datetime(6) NOT NULL,
  modified datetime(6) NOT NULL,
  title varchar(100) NOT NULL,
  url varchar(500) NOT NULL,
  section varchar(20) NOT NULL,
  icon varchar(50) NOT NULL,
  open_in_new_tab tinyint(1) NOT NULL,
  order int unsigned NOT NULL,
  is_active tinyint(1) NOT NULL,
  PRIMARY KEY (id),
  KEY cms_footerl_section_3d1350_idx (section,is_active,order),
  CONSTRAINT cms_footerlink_chk_1 CHECK ((order >= 0))
)   
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table cms_norsucampus
--

DROP TABLE IF EXISTS cms_norsucampus;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE cms_norsucampus (
  id bigint NOT NULL ,
  created datetime(6) NOT NULL,
  modified datetime(6) NOT NULL,
  name varchar(200) NOT NULL,
  location varchar(200) NOT NULL,
  description longtext NOT NULL,
  image varchar(100) NOT NULL,
  order int unsigned NOT NULL,
  is_active tinyint(1) NOT NULL,
  PRIMARY KEY (id),
  CONSTRAINT cms_norsucampus_chk_1 CHECK ((order >= 0))
)  
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table cms_norsuofficial
--

DROP TABLE IF EXISTS cms_norsuofficial;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE cms_norsuofficial (
  id bigint NOT NULL ,
  created datetime(6) NOT NULL,
  modified datetime(6) NOT NULL,
  name varchar(200) NOT NULL,
  position varchar(200) NOT NULL,
  position_level int NOT NULL,
  department varchar(200) NOT NULL,
  bio longtext NOT NULL,
  image varchar(100) DEFAULT NULL,
  email varchar(254) NOT NULL,
  phone varchar(50) NOT NULL,
  order int unsigned NOT NULL,
  is_active tinyint(1) NOT NULL,
  PRIMARY KEY (id),
  KEY cms_norsuof_positio_519377_idx (position_level,is_active,order),
  CONSTRAINT cms_norsuofficial_chk_1 CHECK ((order >= 0))
)  
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table cms_norsuvmgohistory
--

DROP TABLE IF EXISTS cms_norsuvmgohistory;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE cms_norsuvmgohistory (
  id bigint NOT NULL ,
  created datetime(6) NOT NULL,
  modified datetime(6) NOT NULL,
  vision longtext NOT NULL,
  mission longtext NOT NULL,
  goals longtext NOT NULL,
  core_values longtext NOT NULL,
  quality_policy longtext NOT NULL,
  history_brief longtext NOT NULL,
  history_full longtext NOT NULL,
  establishment_year varchar(10) NOT NULL,
  university_status_year varchar(10) NOT NULL,
  show_on_homepage tinyint(1) NOT NULL,
  show_history_on_homepage tinyint(1) NOT NULL,
  about_content longtext NOT NULL DEFAULT (_utf8mb4'Negros Oriental State University (NORSU) is a premier state university in the Philippines, committed to providing quality education and fostering excellence in research, extension, and production services.'),
  about_title varchar(100) NOT NULL,
  goals_title varchar(100) NOT NULL,
  is_active tinyint(1) NOT NULL,
  mission_title varchar(100) NOT NULL,
  section_title varchar(200) NOT NULL,
  values_title varchar(100) NOT NULL,
  vision_title varchar(100) NOT NULL,
  quality_objective_1 longtext NOT NULL DEFAULT (_utf8mb4'Organize Alumni Research and Development to support the quality program based'),
  quality_objective_2 longtext NOT NULL DEFAULT (_utf8mb4'Develop support and good will of the Alumni to institutional and program activities;'),
  quality_objective_3 longtext NOT NULL DEFAULT (_utf8mb4'Achieve professional network and partnership between Alumni communities; and'),
  quality_objective_4 longtext NOT NULL DEFAULT (_utf8mb4'Assure quality services for the Alumni; the Alumni community and the University.'),
  quality_objectives_footer longtext NOT NULL DEFAULT (_utf8mb4'In compliance with the applicable regulatory requirements and continual improvement of its management System'),
  quality_objectives_title varchar(100) NOT NULL,
  PRIMARY KEY (id)
)   
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table cms_pagesection
--

DROP TABLE IF EXISTS cms_pagesection;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE cms_pagesection (
  id bigint NOT NULL ,
  created datetime(6) NOT NULL,
  modified datetime(6) NOT NULL,
  section_type varchar(20) NOT NULL,
  title varchar(200) NOT NULL,
  subtitle longtext NOT NULL,
  content longtext NOT NULL,
  image varchar(100) DEFAULT NULL,
  order int unsigned NOT NULL,
  is_active tinyint(1) NOT NULL,
  PRIMARY KEY (id),
  KEY cms_pagesec_section_73b6c9_idx (section_type,is_active),
  KEY cms_pagesec_order_3d28ca_idx (order),
  CONSTRAINT cms_pagesection_chk_1 CHECK ((order >= 0))
)   
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table cms_siteconfig
--

DROP TABLE IF EXISTS cms_siteconfig;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE cms_siteconfig (
  id bigint NOT NULL ,
  created datetime(6) NOT NULL,
  modified datetime(6) NOT NULL,
  site_name varchar(200) NOT NULL,
  site_tagline longtext NOT NULL,
  logo varchar(100) DEFAULT NULL,
  contact_email varchar(254) NOT NULL,
  contact_phone varchar(50) NOT NULL,
  contact_address longtext NOT NULL,
  facebook_url varchar(200) DEFAULT NULL,
  twitter_url varchar(200) DEFAULT NULL,
  linkedin_url varchar(200) DEFAULT NULL,
  instagram_url varchar(200) DEFAULT NULL,
  youtube_url varchar(200) DEFAULT NULL,
  signup_button_text varchar(100) NOT NULL,
  login_button_text varchar(100) NOT NULL,
  hero_alumni_count varchar(50) NOT NULL,
  hero_countries_count varchar(50) NOT NULL,
  hero_headline varchar(200) NOT NULL,
  hero_microcopy varchar(200) NOT NULL,
  hero_opportunities_count varchar(50) NOT NULL,
  hero_primary_cta_text varchar(100) NOT NULL,
  hero_secondary_cta_text varchar(100) NOT NULL,
  hero_subheadline longtext NOT NULL DEFAULT (_utf8mb4'Access exclusive job opportunities, industry mentorship, and a network of alumni leaders across 30+ countries.'),
  hero_variant varchar(50) NOT NULL,
  hero_background_image varchar(100) DEFAULT NULL,
  PRIMARY KEY (id)
)   
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table cms_staffmember
--

DROP TABLE IF EXISTS cms_staffmember;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE cms_staffmember (
  id bigint NOT NULL ,
  created datetime(6) NOT NULL,
  modified datetime(6) NOT NULL,
  name varchar(200) NOT NULL,
  position varchar(200) NOT NULL,
  department varchar(200) NOT NULL,
  bio longtext NOT NULL,
  image varchar(100) DEFAULT NULL,
  email varchar(254) NOT NULL,
  order int unsigned NOT NULL,
  is_active tinyint(1) NOT NULL,
  PRIMARY KEY (id),
  CONSTRAINT cms_staffmember_chk_1 CHECK ((order >= 0))
)   
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table cms_testimonial
--

DROP TABLE IF EXISTS cms_testimonial;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE cms_testimonial (
  id bigint NOT NULL ,
  created datetime(6) NOT NULL,
  modified datetime(6) NOT NULL,
  name varchar(200) NOT NULL,
  position varchar(200) NOT NULL,
  company varchar(200) NOT NULL,
  quote longtext NOT NULL,
  image varchar(100) DEFAULT NULL,
  order int unsigned NOT NULL,
  is_active tinyint(1) NOT NULL,
  PRIMARY KEY (id),
  CONSTRAINT cms_testimonial_chk_1 CHECK ((order >= 0))
)   
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table cms_timelineitem
--

DROP TABLE IF EXISTS cms_timelineitem;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE cms_timelineitem (
  id bigint NOT NULL ,
  created datetime(6) NOT NULL,
  modified datetime(6) NOT NULL,
  year varchar(10) NOT NULL,
  title varchar(200) NOT NULL,
  description longtext NOT NULL,
  icon varchar(50) NOT NULL,
  order int unsigned NOT NULL,
  is_active tinyint(1) NOT NULL,
  PRIMARY KEY (id),
  CONSTRAINT cms_timelineitem_chk_1 CHECK ((order >= 0))
)   
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table connections_connection
--

DROP TABLE IF EXISTS connections_connection;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE connections_connection (
  id bigint NOT NULL ,
  status varchar(10) NOT NULL,
  created_at datetime(6) NOT NULL,
  updated_at datetime(6) NOT NULL,
  accepted_at datetime(6) DEFAULT NULL,
  receiver_id int NOT NULL,
  requester_id int NOT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY connections_connection_requester_id_receiver_id_c7a4a58e_uniq (requester_id,receiver_id),
  KEY connections_connection_receiver_id_9730caeb_fk_auth_user_id (receiver_id),
  CONSTRAINT connections_connection_receiver_id_9730caeb_fk_auth_user_id FOREIGN KEY (receiver_id) REFERENCES auth_user (id),
  CONSTRAINT connections_connection_requester_id_437bab48_fk_auth_user_id FOREIGN KEY (requester_id) REFERENCES auth_user (id)
)   
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table connections_directconversation
--

DROP TABLE IF EXISTS connections_directconversation;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE connections_directconversation (
  id bigint NOT NULL ,
  created_at datetime(6) NOT NULL,
  updated_at datetime(6) NOT NULL,
  conversation_type varchar(10) NOT NULL,
  created_by_id int DEFAULT NULL,
  group_name varchar(100) DEFAULT NULL,
  group_photo varchar(100) DEFAULT NULL,
  PRIMARY KEY (id),
  KEY connections_directco_created_by_id_5a3622ea_fk_auth_user (created_by_id),
  CONSTRAINT connections_directco_created_by_id_5a3622ea_fk_auth_user FOREIGN KEY (created_by_id) REFERENCES auth_user (id)
)   
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table connections_directconversation_participants
--

DROP TABLE IF EXISTS connections_directconversation_participants;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE connections_directconversation_participants (
  id bigint NOT NULL ,
  directconversation_id bigint NOT NULL,
  user_id int NOT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY connections_directconver_directconversation_id_us_fda7a560_uniq (directconversation_id,user_id),
  KEY connections_directco_user_id_ada8232c_fk_auth_user (user_id),
  CONSTRAINT connections_directco_directconversation_i_0147aa6e_fk_connectio FOREIGN KEY (directconversation_id) REFERENCES connections_directconversation (id),
  CONSTRAINT connections_directco_user_id_ada8232c_fk_auth_user FOREIGN KEY (user_id) REFERENCES auth_user (id)
)   
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table connections_directmessage
--

DROP TABLE IF EXISTS connections_directmessage;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE connections_directmessage (
  id bigint NOT NULL ,
  content longtext NOT NULL,
  attachment varchar(100) DEFAULT NULL,
  is_read tinyint(1) NOT NULL,
  created_at datetime(6) NOT NULL,
  conversation_id bigint NOT NULL,
  sender_id int NOT NULL,
  PRIMARY KEY (id),
  KEY connections_directme_conversation_id_b611b44c_fk_connectio (conversation_id),
  KEY connections_directmessage_sender_id_0c2a3443_fk_auth_user_id (sender_id),
  CONSTRAINT connections_directme_conversation_id_b611b44c_fk_connectio FOREIGN KEY (conversation_id) REFERENCES connections_directconversation (id),
  CONSTRAINT connections_directmessage_sender_id_0c2a3443_fk_auth_user_id FOREIGN KEY (sender_id) REFERENCES auth_user (id)
)   
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table core_address
--

DROP TABLE IF EXISTS core_address;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE core_address (
  id bigint NOT NULL ,
  address_type varchar(10) NOT NULL,
  street_address varchar(255) NOT NULL,
  city varchar(100) NOT NULL,
  state varchar(100) NOT NULL,
  country varchar(2) NOT NULL,
  postal_code varchar(20) NOT NULL,
  is_primary tinyint(1) NOT NULL,
  is_verified tinyint(1) NOT NULL,
  created_at datetime(6) NOT NULL,
  updated_at datetime(6) NOT NULL,
  user_id int NOT NULL,
  PRIMARY KEY (id),
  KEY core_addres_user_id_75f14a_idx (user_id,is_primary),
  KEY core_addres_city_80b6d2_idx (city,state,country),
  CONSTRAINT core_address_user_id_7681a39c_fk_auth_user_id FOREIGN KEY (user_id) REFERENCES auth_user (id)
)  
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table core_brevoconfig
--

DROP TABLE IF EXISTS core_brevoconfig;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE core_brevoconfig (
  id bigint NOT NULL ,
  name varchar(100) NOT NULL,
  api_key varchar(255) NOT NULL,
  api_url varchar(200) NOT NULL,
  from_email varchar(254) NOT NULL,
  from_name varchar(100) NOT NULL,
  is_active tinyint(1) NOT NULL,
  is_verified tinyint(1) NOT NULL,
  created_at datetime(6) NOT NULL,
  updated_at datetime(6) NOT NULL,
  last_tested datetime(6) DEFAULT NULL,
  test_result longtext NOT NULL,
  PRIMARY KEY (id)
)   
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table core_comment
--

DROP TABLE IF EXISTS core_comment;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE core_comment (
  id bigint NOT NULL ,
  content longtext NOT NULL,
  created_at datetime(6) NOT NULL,
  updated_at datetime(6) NOT NULL,
  is_approved tinyint(1) NOT NULL,
  author_id int NOT NULL,
  parent_id bigint DEFAULT NULL,
  post_id bigint NOT NULL,
  PRIMARY KEY (id),
  KEY core_commen_post_id_0d7c44_idx (post_id,created_at),
  KEY core_commen_author__a55bfb_idx (author_id,created_at),
  KEY core_comment_parent_id_1b4ed377_fk_core_comment_id (parent_id),
  CONSTRAINT core_comment_author_id_f7066c5e_fk_auth_user_id FOREIGN KEY (author_id) REFERENCES auth_user (id),
  CONSTRAINT core_comment_parent_id_1b4ed377_fk_core_comment_id FOREIGN KEY (parent_id) REFERENCES core_comment (id),
  CONSTRAINT core_comment_post_id_a75a789c_fk_core_post_id FOREIGN KEY (post_id) REFERENCES core_post (id)
)  
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table core_contactinfo
--

DROP TABLE IF EXISTS core_contactinfo;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE core_contactinfo (
  id bigint NOT NULL ,
  contact_type varchar(20) NOT NULL,
  contact_value varchar(255) NOT NULL,
  is_primary tinyint(1) NOT NULL,
  is_verified tinyint(1) NOT NULL,
  is_public tinyint(1) NOT NULL,
  created_at datetime(6) NOT NULL,
  updated_at datetime(6) NOT NULL,
  user_id int NOT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY core_contactinfo_user_id_contact_type_con_6e2d029d_uniq (user_id,contact_type,contact_value),
  KEY core_contac_user_id_e9744d_idx (user_id,contact_type,is_primary),
  CONSTRAINT core_contactinfo_user_id_c66fea54_fk_auth_user_id FOREIGN KEY (user_id) REFERENCES auth_user (id)
)  
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table core_emailprovider
--

DROP TABLE IF EXISTS core_emailprovider;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE core_emailprovider (
  id bigint NOT NULL ,
  provider_type varchar(10) NOT NULL,
  is_active tinyint(1) NOT NULL,
  created_at datetime(6) NOT NULL,
  updated_at datetime(6) NOT NULL,
  last_used datetime(6) DEFAULT NULL,
  emails_sent int unsigned NOT NULL,
  last_error longtext NOT NULL,
  PRIMARY KEY (id),
  CONSTRAINT core_emailprovider_chk_1 CHECK ((emails_sent >= 0))
)   
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table core_engagementscore
--

DROP TABLE IF EXISTS core_engagementscore;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE core_engagementscore (
  id bigint NOT NULL ,
  created datetime(6) NOT NULL,
  modified datetime(6) NOT NULL,
  total_points int unsigned NOT NULL,
  level int unsigned NOT NULL,
  last_activity datetime(6) DEFAULT NULL,
  user_id int NOT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY user_id (user_id),
  CONSTRAINT core_engagementscore_user_id_b94001c0_fk_auth_user_id FOREIGN KEY (user_id) REFERENCES auth_user (id),
  CONSTRAINT core_engagementscore_chk_1 CHECK ((total_points >= 0)),
  CONSTRAINT core_engagementscore_chk_2 CHECK ((level >= 0))
)  
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table core_notification
--

DROP TABLE IF EXISTS core_notification;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE core_notification (
  id bigint NOT NULL ,
  notification_type varchar(35) NOT NULL,
  object_id int unsigned DEFAULT NULL,
  title varchar(255) NOT NULL,
  message longtext NOT NULL,
  is_read tinyint(1) NOT NULL,
  created_at datetime(6) NOT NULL,
  read_at datetime(6) DEFAULT NULL,
  action_url varchar(200) DEFAULT NULL,
  content_type_id int DEFAULT NULL,
  recipient_id int NOT NULL,
  sender_id int DEFAULT NULL,
  PRIMARY KEY (id),
  KEY core_notification_content_type_id_52a18153_fk_django_co (content_type_id),
  KEY core_notification_sender_id_7af58206_fk_auth_user_id (sender_id),
  KEY core_notifi_recipie_4d7e73_idx (recipient_id,created_at DESC),
  KEY core_notifi_recipie_aeffaf_idx (recipient_id,is_read),
  KEY core_notifi_notific_38b6f7_idx (notification_type,created_at DESC),
  CONSTRAINT core_notification_content_type_id_52a18153_fk_django_co FOREIGN KEY (content_type_id) REFERENCES django_content_type (id),
  CONSTRAINT core_notification_recipient_id_24a3d95c_fk_auth_user_id FOREIGN KEY (recipient_id) REFERENCES auth_user (id),
  CONSTRAINT core_notification_sender_id_7af58206_fk_auth_user_id FOREIGN KEY (sender_id) REFERENCES auth_user (id),
  CONSTRAINT core_notification_chk_1 CHECK ((object_id >= 0))
)   
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table core_notificationpreference
--

DROP TABLE IF EXISTS core_notificationpreference;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE core_notificationpreference (
  id bigint NOT NULL ,
  email_announcements tinyint(1) NOT NULL,
  email_events tinyint(1) NOT NULL,
  email_surveys tinyint(1) NOT NULL,
  email_job_postings tinyint(1) NOT NULL,
  email_connections tinyint(1) NOT NULL,
  email_mentorship tinyint(1) NOT NULL,
  email_messages tinyint(1) NOT NULL,
  app_announcements tinyint(1) NOT NULL,
  app_events tinyint(1) NOT NULL,
  app_surveys tinyint(1) NOT NULL,
  app_job_postings tinyint(1) NOT NULL,
  app_connections tinyint(1) NOT NULL,
  app_mentorship tinyint(1) NOT NULL,
  app_messages tinyint(1) NOT NULL,
  created_at datetime(6) NOT NULL,
  updated_at datetime(6) NOT NULL,
  user_id int NOT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY user_id (user_id),
  CONSTRAINT core_notificationpreference_user_id_0f545da2_fk_auth_user_id FOREIGN KEY (user_id) REFERENCES auth_user (id)
)  
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table core_organizationschema
--

DROP TABLE IF EXISTS core_organizationschema;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE core_organizationschema (
  id bigint NOT NULL ,
  name varchar(255) NOT NULL,
  logo varchar(200) NOT NULL,
  url varchar(200) NOT NULL,
  telephone varchar(50) NOT NULL,
  email varchar(254) NOT NULL,
  street_address varchar(255) NOT NULL,
  address_locality varchar(100) NOT NULL,
  address_region varchar(100) NOT NULL,
  postal_code varchar(20) NOT NULL,
  address_country varchar(2) NOT NULL,
  is_active tinyint(1) NOT NULL,
  PRIMARY KEY (id)
)   
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table core_pageseo
--

DROP TABLE IF EXISTS core_pageseo;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE core_pageseo (
  id bigint NOT NULL ,
  page_path varchar(255) NOT NULL,
  meta_title varchar(60) NOT NULL,
  meta_description varchar(160) NOT NULL,
  meta_keywords varchar(255) NOT NULL,
  og_image varchar(100) DEFAULT NULL,
  twitter_image varchar(100) DEFAULT NULL,
  canonical_url varchar(200) NOT NULL,
  sitemap_priority decimal(2,1) NOT NULL,
  sitemap_changefreq varchar(20) NOT NULL,
  is_active tinyint(1) NOT NULL,
  created_at datetime(6) NOT NULL,
  updated_at datetime(6) NOT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY page_path (page_path)
)   
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table core_post
--

DROP TABLE IF EXISTS core_post;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE core_post (
  id bigint NOT NULL ,
  title varchar(200) NOT NULL,
  content longtext NOT NULL,
  image varchar(100) DEFAULT NULL,
  created_at datetime(6) NOT NULL,
  updated_at datetime(6) NOT NULL,
  is_published tinyint(1) NOT NULL,
  view_count int NOT NULL,
  author_id int NOT NULL,
  PRIMARY KEY (id),
  KEY core_post_author__a786a4_idx (author_id,created_at),
  KEY core_post_is_publ_01104b_idx (is_published),
  CONSTRAINT core_post_author_id_083b751e_fk_auth_user_id FOREIGN KEY (author_id) REFERENCES auth_user (id)
)  
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table core_reaction
--

DROP TABLE IF EXISTS core_reaction;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE core_reaction (
  id bigint NOT NULL ,
  reaction_type varchar(10) NOT NULL,
  created_at datetime(6) NOT NULL,
  updated_at datetime(6) NOT NULL,
  post_id bigint NOT NULL,
  user_id int NOT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY core_reaction_user_id_post_id_fa70eec8_uniq (user_id,post_id),
  KEY core_reacti_post_id_c38b9c_idx (post_id,reaction_type),
  KEY core_reacti_user_id_31a201_idx (user_id,created_at),
  CONSTRAINT core_reaction_post_id_1f5b4eb2_fk_core_post_id FOREIGN KEY (post_id) REFERENCES core_post (id),
  CONSTRAINT core_reaction_user_id_968339ea_fk_auth_user_id FOREIGN KEY (user_id) REFERENCES auth_user (id)
)  
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table core_recaptchaconfig
--

DROP TABLE IF EXISTS core_recaptchaconfig;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE core_recaptchaconfig (
  id bigint NOT NULL ,
  name varchar(100) NOT NULL,
  site_key varchar(200) NOT NULL,
  secret_key varchar(200) NOT NULL,
  version varchar(10) NOT NULL,
  threshold double NOT NULL,
  is_active tinyint(1) NOT NULL,
  created_at datetime(6) NOT NULL,
  updated_at datetime(6) NOT NULL,
  enabled tinyint(1) NOT NULL,
  PRIMARY KEY (id)
)   
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table core_smtpconfig
--

DROP TABLE IF EXISTS core_smtpconfig;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE core_smtpconfig (
  id bigint NOT NULL ,
  name varchar(100) NOT NULL,
  host varchar(255) NOT NULL,
  port int unsigned NOT NULL,
  use_tls tinyint(1) NOT NULL,
  use_ssl tinyint(1) NOT NULL,
  username varchar(254) NOT NULL,
  password varchar(255) NOT NULL,
  from_email varchar(254) NOT NULL,
  from_name varchar(100) NOT NULL,
  is_active tinyint(1) NOT NULL,
  is_verified tinyint(1) NOT NULL,
  created_at datetime(6) NOT NULL,
  updated_at datetime(6) NOT NULL,
  last_tested datetime(6) DEFAULT NULL,
  test_result longtext NOT NULL,
  PRIMARY KEY (id),
  CONSTRAINT core_smtpconfig_chk_1 CHECK ((port >= 0))
)  
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table core_ssoconfig
--

DROP TABLE IF EXISTS core_ssoconfig;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE core_ssoconfig (
  id bigint NOT NULL ,
  name varchar(100) NOT NULL,
  provider varchar(20) NOT NULL,
  client_id varchar(500) NOT NULL,
  secret_key varchar(500) NOT NULL,
  scopes longtext NOT NULL,
  verified_email tinyint(1) NOT NULL,
  is_active tinyint(1) NOT NULL,
  enabled tinyint(1) NOT NULL,
  is_verified tinyint(1) NOT NULL,
  created_at datetime(6) NOT NULL,
  updated_at datetime(6) NOT NULL,
  last_tested datetime(6) DEFAULT NULL,
  test_result longtext NOT NULL,
  login_count int unsigned NOT NULL,
  last_used datetime(6) DEFAULT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY core_ssoconfig_provider_is_active_f114c0a8_uniq (provider,is_active),
  CONSTRAINT core_ssoconfig_chk_1 CHECK ((login_count >= 0))
)   
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table core_userauditlog
--

DROP TABLE IF EXISTS core_userauditlog;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE core_userauditlog (
  id bigint NOT NULL ,
  action varchar(20) NOT NULL,
  timestamp datetime(6) NOT NULL,
  details json NOT NULL,
  reason longtext NOT NULL,
  ip_address char(39) DEFAULT NULL,
  performed_by_id int DEFAULT NULL,
  user_id int NOT NULL,
  PRIMARY KEY (id),
  KEY core_userau_user_id_e53bc6_idx (user_id,timestamp DESC),
  KEY core_userau_action_23bd21_idx (action,timestamp DESC),
  KEY core_userau_perform_6e75b3_idx (performed_by_id,timestamp DESC),
  CONSTRAINT core_userauditlog_performed_by_id_0d6f31c1_fk_auth_user_id FOREIGN KEY (performed_by_id) REFERENCES auth_user (id),
  CONSTRAINT core_userauditlog_user_id_ba31f729_fk_auth_user_id FOREIGN KEY (user_id) REFERENCES auth_user (id)
)   
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table core_userengagement
--

DROP TABLE IF EXISTS core_userengagement;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE core_userengagement (
  id bigint NOT NULL ,
  created datetime(6) NOT NULL,
  modified datetime(6) NOT NULL,
  activity_type varchar(20) NOT NULL,
  points int unsigned NOT NULL,
  description longtext NOT NULL,
  visit_count int NOT NULL,
  total_posts int NOT NULL,
  total_comments int NOT NULL,
  total_reactions int NOT NULL,
  last_activity datetime(6) NOT NULL,
  last_login datetime(6) DEFAULT NULL,
  user_id int NOT NULL,
  PRIMARY KEY (id),
  KEY core_userengagement_user_id_1e3b1978_fk_auth_user_id (user_id),
  CONSTRAINT core_userengagement_user_id_1e3b1978_fk_auth_user_id FOREIGN KEY (user_id) REFERENCES auth_user (id),
  CONSTRAINT core_userengagement_chk_1 CHECK ((points >= 0))
)  
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table core_userstatuschange
--

DROP TABLE IF EXISTS core_userstatuschange;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE core_userstatuschange (
  id bigint NOT NULL ,
  timestamp datetime(6) NOT NULL,
  old_status tinyint(1) NOT NULL,
  new_status tinyint(1) NOT NULL,
  reason longtext NOT NULL,
  ip_address char(39) DEFAULT NULL,
  changed_by_id int DEFAULT NULL,
  user_id int NOT NULL,
  PRIMARY KEY (id),
  KEY core_userst_user_id_d62f30_idx (user_id,timestamp DESC),
  KEY core_userst_changed_6fd479_idx (changed_by_id,timestamp DESC),
  CONSTRAINT core_userstatuschange_changed_by_id_e7faf51b_fk_auth_user_id FOREIGN KEY (changed_by_id) REFERENCES auth_user (id),
  CONSTRAINT core_userstatuschange_user_id_8860ed38_fk_auth_user_id FOREIGN KEY (user_id) REFERENCES auth_user (id)
)  
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table django_admin_log
--

DROP TABLE IF EXISTS django_admin_log;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE django_admin_log (
  id int NOT NULL ,
  action_time datetime(6) NOT NULL,
  object_id longtext,
  object_repr varchar(200) NOT NULL,
  action_flag smallint unsigned NOT NULL,
  change_message longtext NOT NULL,
  content_type_id int DEFAULT NULL,
  user_id int NOT NULL,
  PRIMARY KEY (id),
  KEY django_admin_log_content_type_id_c4bce8eb_fk_django_co (content_type_id),
  KEY django_admin_log_user_id_c564eba6_fk_auth_user_id (user_id),
  CONSTRAINT django_admin_log_content_type_id_c4bce8eb_fk_django_co FOREIGN KEY (content_type_id) REFERENCES django_content_type (id),
  CONSTRAINT django_admin_log_user_id_c564eba6_fk_auth_user_id FOREIGN KEY (user_id) REFERENCES auth_user (id),
  CONSTRAINT django_admin_log_chk_1 CHECK ((action_flag >= 0))
)  
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table django_content_type
--

DROP TABLE IF EXISTS django_content_type;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE django_content_type (
  id int NOT NULL ,
  app_label varchar(100) NOT NULL,
  model varchar(100) NOT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY django_content_type_app_label_model_76bd3d3b_uniq (app_label,model)
)   
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table django_migrations
--

DROP TABLE IF EXISTS django_migrations;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE django_migrations (
  id bigint NOT NULL ,
  app varchar(255) NOT NULL,
  name varchar(255) NOT NULL,
  applied datetime(6) NOT NULL,
  PRIMARY KEY (id)
)   
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table django_session
--

DROP TABLE IF EXISTS django_session;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE django_session (
  session_key varchar(40) NOT NULL,
  session_data longtext NOT NULL,
  expire_date datetime(6) NOT NULL,
  PRIMARY KEY (session_key),
  KEY django_session_expire_date_a5c62663 (expire_date)
)  
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table django_site
--

DROP TABLE IF EXISTS django_site;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE django_site (
  id int NOT NULL ,
  domain varchar(100) NOT NULL,
  name varchar(50) NOT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY django_site_domain_a2e37b91_uniq (domain)
)   
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table donations_blacklistedentity
--

DROP TABLE IF EXISTS donations_blacklistedentity;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE donations_blacklistedentity (
  id bigint NOT NULL ,
  entity_type varchar(15) NOT NULL,
  value varchar(255) NOT NULL,
  reason longtext NOT NULL,
  is_active tinyint(1) NOT NULL,
  created_at datetime(6) NOT NULL,
  expires_at datetime(6) DEFAULT NULL,
  created_by_id int DEFAULT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY donations_blacklistedentity_entity_type_value_8f04282d_uniq (entity_type,value),
  KEY donations_blackliste_created_by_id_9012cd31_fk_auth_user (created_by_id),
  CONSTRAINT donations_blackliste_created_by_id_9012cd31_fk_auth_user FOREIGN KEY (created_by_id) REFERENCES auth_user (id)
)  
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table donations_campaign
--

DROP TABLE IF EXISTS donations_campaign;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE donations_campaign (
  id bigint NOT NULL ,
  name varchar(200) NOT NULL,
  slug varchar(220) NOT NULL,
  description longtext NOT NULL,
  short_description varchar(255) NOT NULL,
  featured_image varchar(100) DEFAULT NULL,
  goal_amount decimal(12,2) NOT NULL,
  current_amount decimal(12,2) NOT NULL,
  start_date datetime(6) NOT NULL,
  end_date datetime(6) DEFAULT NULL,
  status varchar(20) NOT NULL,
  is_featured tinyint(1) NOT NULL,
  created_at datetime(6) NOT NULL,
  updated_at datetime(6) NOT NULL,
  created_by_id int DEFAULT NULL,
  campaign_type_id bigint NOT NULL,
  visibility varchar(20) NOT NULL,
  allow_donations tinyint(1) NOT NULL,
  gcash_config_id bigint DEFAULT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY slug (slug),
  KEY donations_campaign_created_by_id_a242fc32_fk_auth_user_id (created_by_id),
  KEY donations_campaign_campaign_type_id_247b8eca_fk_donations (campaign_type_id),
  KEY donations_campaign_gcash_config_id_cb9e6eec_fk_donations (gcash_config_id),
  CONSTRAINT donations_campaign_campaign_type_id_247b8eca_fk_donations FOREIGN KEY (campaign_type_id) REFERENCES donations_campaigntype (id),
  CONSTRAINT donations_campaign_created_by_id_a242fc32_fk_auth_user_id FOREIGN KEY (created_by_id) REFERENCES auth_user (id),
  CONSTRAINT donations_campaign_gcash_config_id_cb9e6eec_fk_donations FOREIGN KEY (gcash_config_id) REFERENCES donations_gcashconfig (id)
)   
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table donations_campaigntype
--

DROP TABLE IF EXISTS donations_campaigntype;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE donations_campaigntype (
  id bigint NOT NULL ,
  name varchar(100) NOT NULL,
  slug varchar(120) NOT NULL,
  description longtext NOT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY slug (slug)
)   
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table donations_campaignupdate
--

DROP TABLE IF EXISTS donations_campaignupdate;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE donations_campaignupdate (
  id bigint NOT NULL ,
  title varchar(200) NOT NULL,
  content longtext NOT NULL,
  image varchar(100) DEFAULT NULL,
  is_featured tinyint(1) NOT NULL,
  created datetime(6) NOT NULL,
  updated datetime(6) NOT NULL,
  campaign_id bigint NOT NULL,
  created_by_id int DEFAULT NULL,
  PRIMARY KEY (id),
  KEY donations_campaignup_campaign_id_a8275e4c_fk_donations (campaign_id),
  KEY donations_campaignupdate_created_by_id_25334757_fk_auth_user_id (created_by_id),
  CONSTRAINT donations_campaignup_campaign_id_a8275e4c_fk_donations FOREIGN KEY (campaign_id) REFERENCES donations_campaign (id),
  CONSTRAINT donations_campaignupdate_created_by_id_25334757_fk_auth_user_id FOREIGN KEY (created_by_id) REFERENCES auth_user (id)
)  
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table donations_donation
--

DROP TABLE IF EXISTS donations_donation;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE donations_donation (
  id bigint NOT NULL ,
  donor_name varchar(200) NOT NULL,
  donor_email varchar(254) NOT NULL,
  amount decimal(10,2) NOT NULL,
  donation_date datetime(6) NOT NULL,
  status varchar(20) NOT NULL,
  payment_method varchar(20) NOT NULL,
  is_anonymous tinyint(1) NOT NULL,
  message longtext NOT NULL,
  reference_number varchar(100) DEFAULT NULL,
  receipt_sent tinyint(1) NOT NULL,
  created_at datetime(6) NOT NULL,
  updated_at datetime(6) NOT NULL,
  campaign_id bigint NOT NULL,
  donor_id int DEFAULT NULL,
  gcash_transaction_id varchar(50) NOT NULL,
  payment_proof varchar(100) DEFAULT NULL,
  verification_date datetime(6) DEFAULT NULL,
  verification_notes longtext NOT NULL DEFAULT (_utf8mb4''),
  verified_by_id int DEFAULT NULL,
  PRIMARY KEY (id),
  KEY donations_donation_campaign_id_6ee594d5_fk_donations_campaign_id (campaign_id),
  KEY donations_donation_donor_id_25b1f2bc_fk_auth_user_id (donor_id),
  KEY donations_donation_verified_by_id_1d62d7b2_fk_auth_user_id (verified_by_id),
  CONSTRAINT donations_donation_campaign_id_6ee594d5_fk_donations_campaign_id FOREIGN KEY (campaign_id) REFERENCES donations_campaign (id),
  CONSTRAINT donations_donation_donor_id_25b1f2bc_fk_auth_user_id FOREIGN KEY (donor_id) REFERENCES auth_user (id),
  CONSTRAINT donations_donation_verified_by_id_1d62d7b2_fk_auth_user_id FOREIGN KEY (verified_by_id) REFERENCES auth_user (id)
)   
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table donations_donorrecognition
--

DROP TABLE IF EXISTS donations_donorrecognition;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE donations_donorrecognition (
  id bigint NOT NULL ,
  name varchar(100) NOT NULL,
  description longtext NOT NULL,
  minimum_amount decimal(10,2) NOT NULL,
  badge_image varchar(100) DEFAULT NULL,
  is_active tinyint(1) NOT NULL,
  PRIMARY KEY (id)
)  
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table donations_fraudalert
--

DROP TABLE IF EXISTS donations_fraudalert;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE donations_fraudalert (
  id bigint NOT NULL ,
  alert_type varchar(20) NOT NULL,
  severity varchar(10) NOT NULL,
  status varchar(15) NOT NULL,
  description longtext NOT NULL,
  metadata json NOT NULL,
  ip_address char(39) DEFAULT NULL,
  user_agent longtext NOT NULL,
  created_at datetime(6) NOT NULL,
  reviewed_at datetime(6) DEFAULT NULL,
  resolution_notes longtext NOT NULL,
  donation_id bigint NOT NULL,
  reviewed_by_id int DEFAULT NULL,
  PRIMARY KEY (id),
  KEY donations_fraudalert_donation_id_6e2b628d_fk_donations (donation_id),
  KEY donations_fraudalert_reviewed_by_id_d5158a1e_fk_auth_user_id (reviewed_by_id),
  CONSTRAINT donations_fraudalert_donation_id_6e2b628d_fk_donations FOREIGN KEY (donation_id) REFERENCES donations_donation (id),
  CONSTRAINT donations_fraudalert_reviewed_by_id_d5158a1e_fk_auth_user_id FOREIGN KEY (reviewed_by_id) REFERENCES auth_user (id)
)  
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table donations_gcashconfig
--

DROP TABLE IF EXISTS donations_gcashconfig;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE donations_gcashconfig (
  id bigint NOT NULL ,
  name varchar(100) NOT NULL,
  gcash_number varchar(15) NOT NULL,
  account_name varchar(100) NOT NULL,
  qr_code_image varchar(100) NOT NULL,
  is_active tinyint(1) NOT NULL,
  instructions longtext NOT NULL,
  created_at datetime(6) NOT NULL,
  updated_at datetime(6) NOT NULL,
  PRIMARY KEY (id)
)   
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table events_event
--

DROP TABLE IF EXISTS events_event;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE events_event (
  id bigint NOT NULL ,
  title varchar(200) NOT NULL,
  description longtext NOT NULL,
  start_date datetime(6) NOT NULL,
  end_date datetime(6) NOT NULL,
  location varchar(200) NOT NULL,
  is_virtual tinyint(1) NOT NULL,
  virtual_link varchar(200) DEFAULT NULL,
  max_participants int unsigned DEFAULT NULL,
  status varchar(20) NOT NULL,
  created_at datetime(6) NOT NULL,
  updated_at datetime(6) NOT NULL,
  image varchar(100) DEFAULT NULL,
  created_by_id int NOT NULL,
  visibility varchar(10) NOT NULL,
  PRIMARY KEY (id),
  KEY events_event_created_by_id_2c28ea90_fk_auth_user_id (created_by_id),
  CONSTRAINT events_event_created_by_id_2c28ea90_fk_auth_user_id FOREIGN KEY (created_by_id) REFERENCES auth_user (id),
  CONSTRAINT events_event_chk_1 CHECK ((max_participants >= 0))
)   
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table events_event_notified_groups
--

DROP TABLE IF EXISTS events_event_notified_groups;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE events_event_notified_groups (
  id bigint NOT NULL ,
  event_id bigint NOT NULL,
  alumnigroup_id bigint NOT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY events_event_notified_gr_event_id_alumnigroup_id_f63c83ca_uniq (event_id,alumnigroup_id),
  KEY events_event_notifie_alumnigroup_id_d47843c2_fk_alumni_gr (alumnigroup_id),
  CONSTRAINT events_event_notifie_alumnigroup_id_d47843c2_fk_alumni_gr FOREIGN KEY (alumnigroup_id) REFERENCES alumni_groups_alumnigroup (id),
  CONSTRAINT events_event_notifie_event_id_62b4531f_fk_events_ev FOREIGN KEY (event_id) REFERENCES events_event (id)
)  
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table events_eventrsvp
--

DROP TABLE IF EXISTS events_eventrsvp;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE events_eventrsvp (
  id bigint NOT NULL ,
  status varchar(5) NOT NULL,
  created_at datetime(6) NOT NULL,
  updated_at datetime(6) NOT NULL,
  notes longtext NOT NULL,
  event_id bigint NOT NULL,
  user_id int NOT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY events_eventrsvp_event_id_user_id_426c48bb_uniq (event_id,user_id),
  KEY events_eventrsvp_user_id_6ba93060_fk_auth_user_id (user_id),
  CONSTRAINT events_eventrsvp_event_id_052def65_fk_events_event_id FOREIGN KEY (event_id) REFERENCES events_event (id),
  CONSTRAINT events_eventrsvp_user_id_6ba93060_fk_auth_user_id FOREIGN KEY (user_id) REFERENCES auth_user (id)
)   
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table feedback_feedback
--

DROP TABLE IF EXISTS feedback_feedback;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE feedback_feedback (
  id bigint NOT NULL ,
  category varchar(20) NOT NULL,
  subject varchar(200) NOT NULL,
  message longtext NOT NULL,
  priority varchar(20) NOT NULL,
  status varchar(20) NOT NULL,
  admin_notes longtext NOT NULL,
  attachment varchar(100) DEFAULT NULL,
  created_at datetime(6) NOT NULL,
  updated_at datetime(6) NOT NULL,
  user_id int DEFAULT NULL,
  PRIMARY KEY (id),
  KEY feedback_feedback_user_id_f7dd5014_fk_auth_user_id (user_id),
  CONSTRAINT feedback_feedback_user_id_f7dd5014_fk_auth_user_id FOREIGN KEY (user_id) REFERENCES auth_user (id)
)   
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table jobs_jobapplication
--

DROP TABLE IF EXISTS jobs_jobapplication;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE jobs_jobapplication (
  id bigint NOT NULL ,
  application_date datetime(6) NOT NULL,
  status varchar(20) NOT NULL,
  cover_letter longtext,
  resume varchar(100) NOT NULL,
  additional_documents varchar(100) DEFAULT NULL,
  notes longtext,
  last_updated datetime(6) NOT NULL,
  applicant_id int NOT NULL,
  job_id bigint NOT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY jobs_jobapplication_job_id_applicant_id_f83e8769_uniq (job_id,applicant_id),
  KEY jobs_jobapplication_applicant_id_7f41cf6a_fk_auth_user_id (applicant_id),
  CONSTRAINT jobs_jobapplication_applicant_id_7f41cf6a_fk_auth_user_id FOREIGN KEY (applicant_id) REFERENCES auth_user (id),
  CONSTRAINT jobs_jobapplication_job_id_625fd19d_fk_jobs_jobposting_id FOREIGN KEY (job_id) REFERENCES jobs_jobposting (id)
)  
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table jobs_jobposting
--

DROP TABLE IF EXISTS jobs_jobposting;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE jobs_jobposting (
  id bigint NOT NULL ,
  job_title varchar(200) NOT NULL,
  slug varchar(250) NOT NULL,
  company_name varchar(200) NOT NULL,
  location varchar(200) NOT NULL,
  job_type varchar(20) NOT NULL,
  job_description longtext NOT NULL,
  requirements longtext NOT NULL,
  responsibilities longtext NOT NULL,
  experience_level varchar(20) NOT NULL,
  skills_required longtext NOT NULL,
  education_requirements longtext NOT NULL,
  benefits longtext NOT NULL,
  application_link varchar(500) DEFAULT NULL,
  salary_range varchar(100) DEFAULT NULL,
  posted_date datetime(6) NOT NULL,
  is_featured tinyint(1) NOT NULL,
  is_active tinyint(1) NOT NULL,
  source varchar(50) NOT NULL,
  source_type varchar(20) NOT NULL,
  accepts_internal_applications tinyint(1) NOT NULL,
  posted_by_id int DEFAULT NULL,
  category varchar(50) NOT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY slug (slug),
  KEY jobs_jobpos_job_typ_fa6fc4_idx (job_type),
  KEY jobs_jobpos_posted__2014b9_idx (posted_date),
  KEY jobs_jobpos_is_feat_3126c5_idx (is_featured),
  KEY jobs_jobpos_source__7a2f04_idx (source_type),
  KEY jobs_jobposting_posted_by_id_3d191c74_fk_auth_user_id (posted_by_id),
  KEY jobs_jobpos_source_9226ee_idx (source),
  CONSTRAINT jobs_jobposting_posted_by_id_3d191c74_fk_auth_user_id FOREIGN KEY (posted_by_id) REFERENCES auth_user (id)
)  
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table jobs_requireddocument
--

DROP TABLE IF EXISTS jobs_requireddocument;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE jobs_requireddocument (
  id bigint NOT NULL ,
  name varchar(100) NOT NULL,
  document_type varchar(20) NOT NULL,
  description longtext NOT NULL,
  is_required tinyint(1) NOT NULL,
  file_types varchar(200) NOT NULL,
  max_file_size int NOT NULL,
  job_id bigint NOT NULL,
  PRIMARY KEY (id),
  KEY jobs_requireddocument_job_id_54208415_fk_jobs_jobposting_id (job_id),
  CONSTRAINT jobs_requireddocument_job_id_54208415_fk_jobs_jobposting_id FOREIGN KEY (job_id) REFERENCES jobs_jobposting (id)
)  
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table jobs_scrapedjob
--

DROP TABLE IF EXISTS jobs_scrapedjob;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE jobs_scrapedjob (
  id bigint NOT NULL ,
  search_keyword varchar(200) NOT NULL,
  search_location varchar(200) NOT NULL,
  source varchar(20) NOT NULL,
  scraped_data json NOT NULL,
  total_found int NOT NULL,
  scraped_at datetime(6) NOT NULL,
  is_active tinyint(1) NOT NULL,
  scraped_by_id int NOT NULL,
  PRIMARY KEY (id),
  KEY jobs_scrapedjob_scraped_by_id_cd4104f9_fk_auth_user_id (scraped_by_id),
  KEY jobs_scrape_search__e7bcab_idx (search_keyword),
  KEY jobs_scrape_search__1f457d_idx (search_location),
  KEY jobs_scrape_source_a0eda1_idx (source),
  KEY jobs_scrape_scraped_141fa2_idx (scraped_at),
  CONSTRAINT jobs_scrapedjob_scraped_by_id_cd4104f9_fk_auth_user_id FOREIGN KEY (scraped_by_id) REFERENCES auth_user (id)
)  
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table location_tracking_locationdata
--

DROP TABLE IF EXISTS location_tracking_locationdata;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE location_tracking_locationdata (
  id bigint NOT NULL ,
  latitude decimal(9,6) NOT NULL,
  longitude decimal(9,6) NOT NULL,
  timestamp datetime(6) NOT NULL,
  is_active tinyint(1) NOT NULL,
  user_id int NOT NULL,
  PRIMARY KEY (id),
  KEY location_tracking_locationdata_user_id_941869a3_fk_auth_user_id (user_id),
  CONSTRAINT location_tracking_locationdata_user_id_941869a3_fk_auth_user_id FOREIGN KEY (user_id) REFERENCES auth_user (id)
)   
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table log_viewer_archivestorageconfig
--

DROP TABLE IF EXISTS log_viewer_archivestorageconfig;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE log_viewer_archivestorageconfig (
  id bigint NOT NULL ,
  max_storage_gb decimal(10,2) NOT NULL,
  warning_threshold_percent int NOT NULL,
  critical_threshold_percent int NOT NULL,
  current_size_gb decimal(10,2) NOT NULL,
  last_size_check datetime(6) DEFAULT NULL,
  created_at datetime(6) NOT NULL,
  updated_at datetime(6) NOT NULL,
  PRIMARY KEY (id)
)   
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table log_viewer_auditlog
--

DROP TABLE IF EXISTS log_viewer_auditlog;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE log_viewer_auditlog (
  id bigint NOT NULL ,
  object_id int unsigned NOT NULL,
  action varchar(10) NOT NULL,
  model_name varchar(100) NOT NULL,
  app_label varchar(50) NOT NULL,
  username varchar(150) DEFAULT NULL,
  old_values json DEFAULT NULL,
  new_values json DEFAULT NULL,
  changed_fields json DEFAULT NULL,
  ip_address char(39) DEFAULT NULL,
  user_agent longtext,
  request_path varchar(500) DEFAULT NULL,
  message longtext NOT NULL,
  timestamp datetime(6) NOT NULL,
  content_type_id int NOT NULL,
  user_id int DEFAULT NULL,
  PRIMARY KEY (id),
  KEY log_viewer_auditlog_content_type_id_693f78b8_fk_django_co (content_type_id),
  KEY log_viewer_auditlog_model_name_db88ba12 (model_name),
  KEY log_viewer_auditlog_app_label_851435e5 (app_label),
  KEY log_viewer_auditlog_timestamp_5fe893dc (timestamp),
  KEY log_viewer__timesta_7d6a48_idx (timestamp DESC,action),
  KEY log_viewer__model_n_f4f79b_idx (model_name,app_label),
  KEY log_viewer__user_id_f8bdec_idx (user_id,timestamp),
  CONSTRAINT log_viewer_auditlog_content_type_id_693f78b8_fk_django_co FOREIGN KEY (content_type_id) REFERENCES django_content_type (id),
  CONSTRAINT log_viewer_auditlog_user_id_702b80dc_fk_auth_user_id FOREIGN KEY (user_id) REFERENCES auth_user (id),
  CONSTRAINT log_viewer_auditlog_chk_1 CHECK ((object_id >= 0))
)   
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table log_viewer_logcleanupschedule
--

DROP TABLE IF EXISTS log_viewer_logcleanupschedule;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE log_viewer_logcleanupschedule (
  id bigint NOT NULL ,
  enabled tinyint(1) NOT NULL,
  frequency varchar(10) NOT NULL,
  execution_time time(6) NOT NULL,
  day_of_week int DEFAULT NULL,
  day_of_month int DEFAULT NULL,
  last_run datetime(6) DEFAULT NULL,
  next_run datetime(6) DEFAULT NULL,
  created_at datetime(6) NOT NULL,
  updated_at datetime(6) NOT NULL,
  PRIMARY KEY (id)
)  
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table log_viewer_logoperationhistory
--

DROP TABLE IF EXISTS log_viewer_logoperationhistory;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE log_viewer_logoperationhistory (
  id bigint NOT NULL ,
  operation_type varchar(10) NOT NULL,
  status varchar(10) NOT NULL,
  started_at datetime(6) NOT NULL,
  completed_at datetime(6) DEFAULT NULL,
  audit_logs_processed int NOT NULL,
  audit_logs_deleted int NOT NULL,
  file_logs_processed int NOT NULL,
  file_logs_deleted int NOT NULL,
  archives_created int NOT NULL,
  error_message longtext NOT NULL,
  archive_files json NOT NULL,
  triggered_by_id int DEFAULT NULL,
  PRIMARY KEY (id),
  KEY log_viewer_logoperat_triggered_by_id_496e1426_fk_auth_user (triggered_by_id),
  KEY log_viewer__started_6696c9_idx (started_at DESC),
  KEY log_viewer__status_f11816_idx (status,started_at DESC),
  CONSTRAINT log_viewer_logoperat_triggered_by_id_496e1426_fk_auth_user FOREIGN KEY (triggered_by_id) REFERENCES auth_user (id)
)  
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table log_viewer_logretentionpolicy
--

DROP TABLE IF EXISTS log_viewer_logretentionpolicy;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE log_viewer_logretentionpolicy (
  id bigint NOT NULL ,
  log_type varchar(10) NOT NULL,
  enabled tinyint(1) NOT NULL,
  retention_days int unsigned NOT NULL,
  export_before_delete tinyint(1) NOT NULL,
  export_format varchar(10) NOT NULL,
  archive_path varchar(500) NOT NULL,
  created_at datetime(6) NOT NULL,
  updated_at datetime(6) NOT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY log_type (log_type),
  CONSTRAINT log_viewer_logretentionpolicy_chk_1 CHECK ((retention_days >= 0))
)   
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table mentorship_conversation
--

DROP TABLE IF EXISTS mentorship_conversation;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE mentorship_conversation (
  id bigint NOT NULL ,
  created_at datetime(6) NOT NULL,
  updated_at datetime(6) NOT NULL,
  mentorship_id bigint DEFAULT NULL,
  conversation_type varchar(20) NOT NULL,
  participant_1_id int DEFAULT NULL,
  participant_2_id int DEFAULT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY mentorship_id (mentorship_id),
  KEY mentorship_conversat_participant_1_id_e3e6f739_fk_auth_user (participant_1_id),
  KEY mentorship_conversat_participant_2_id_822878d6_fk_auth_user (participant_2_id),
  CONSTRAINT mentorship_conversat_mentorship_id_e67212b3_fk_accounts_ FOREIGN KEY (mentorship_id) REFERENCES accounts_mentorshiprequest (id),
  CONSTRAINT mentorship_conversat_participant_1_id_e3e6f739_fk_auth_user FOREIGN KEY (participant_1_id) REFERENCES auth_user (id),
  CONSTRAINT mentorship_conversat_participant_2_id_822878d6_fk_auth_user FOREIGN KEY (participant_2_id) REFERENCES auth_user (id)
)  
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table mentorship_mentorshipgoal
--

DROP TABLE IF EXISTS mentorship_mentorshipgoal;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE mentorship_mentorshipgoal (
  id bigint NOT NULL ,
  title varchar(200) NOT NULL,
  description longtext NOT NULL,
  priority varchar(20) NOT NULL,
  status varchar(20) NOT NULL,
  target_date date DEFAULT NULL,
  completion_date date DEFAULT NULL,
  created_at datetime(6) NOT NULL,
  updated_at datetime(6) NOT NULL,
  created_by_id int NOT NULL,
  mentorship_id bigint NOT NULL,
  PRIMARY KEY (id),
  KEY mentorship_mentorshipgoal_created_by_id_f19e1fac_fk_auth_user_id (created_by_id),
  KEY mentorship_mentorshi_mentorship_id_3b1a0146_fk_accounts_ (mentorship_id),
  CONSTRAINT mentorship_mentorshi_mentorship_id_3b1a0146_fk_accounts_ FOREIGN KEY (mentorship_id) REFERENCES accounts_mentorshiprequest (id),
  CONSTRAINT mentorship_mentorshipgoal_created_by_id_f19e1fac_fk_auth_user_id FOREIGN KEY (created_by_id) REFERENCES auth_user (id)
)  
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table mentorship_mentorshipmeeting
--

DROP TABLE IF EXISTS mentorship_mentorshipmeeting;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE mentorship_mentorshipmeeting (
  id bigint NOT NULL ,
  title varchar(200) NOT NULL,
  description longtext NOT NULL,
  meeting_date datetime(6) NOT NULL,
  duration int NOT NULL,
  meeting_link varchar(200) NOT NULL,
  status varchar(20) NOT NULL,
  notes longtext NOT NULL,
  created_at datetime(6) NOT NULL,
  updated_at datetime(6) NOT NULL,
  mentorship_id bigint NOT NULL,
  PRIMARY KEY (id),
  KEY mentorship_mentorshi_mentorship_id_0069b743_fk_accounts_ (mentorship_id),
  CONSTRAINT mentorship_mentorshi_mentorship_id_0069b743_fk_accounts_ FOREIGN KEY (mentorship_id) REFERENCES accounts_mentorshiprequest (id)
)  
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table mentorship_mentorshipmessage
--

DROP TABLE IF EXISTS mentorship_mentorshipmessage;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE mentorship_mentorshipmessage (
  id bigint NOT NULL ,
  content longtext NOT NULL,
  attachment varchar(100) DEFAULT NULL,
  is_read tinyint(1) NOT NULL,
  created_at datetime(6) NOT NULL,
  mentorship_id bigint NOT NULL,
  sender_id int NOT NULL,
  PRIMARY KEY (id),
  KEY mentorship_mentorshi_mentorship_id_d31e363f_fk_accounts_ (mentorship_id),
  KEY mentorship_mentorshipmessage_sender_id_add35e19_fk_auth_user_id (sender_id),
  CONSTRAINT mentorship_mentorshi_mentorship_id_d31e363f_fk_accounts_ FOREIGN KEY (mentorship_id) REFERENCES accounts_mentorshiprequest (id),
  CONSTRAINT mentorship_mentorshipmessage_sender_id_add35e19_fk_auth_user_id FOREIGN KEY (sender_id) REFERENCES auth_user (id)
)  
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table mentorship_mentorshipmilestone
--

DROP TABLE IF EXISTS mentorship_mentorshipmilestone;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE mentorship_mentorshipmilestone (
  id bigint NOT NULL ,
  title varchar(200) NOT NULL,
  description longtext NOT NULL,
  status varchar(20) NOT NULL,
  target_date date DEFAULT NULL,
  completion_date date DEFAULT NULL,
  created_at datetime(6) NOT NULL,
  updated_at datetime(6) NOT NULL,
  goal_id bigint NOT NULL,
  PRIMARY KEY (id),
  KEY mentorship_mentorshi_goal_id_2e0e534d_fk_mentorshi (goal_id),
  CONSTRAINT mentorship_mentorshi_goal_id_2e0e534d_fk_mentorshi FOREIGN KEY (goal_id) REFERENCES mentorship_mentorshipgoal (id)
)  
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table mentorship_mentorshipprogress
--

DROP TABLE IF EXISTS mentorship_mentorshipprogress;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE mentorship_mentorshipprogress (
  id bigint NOT NULL ,
  title varchar(200) NOT NULL,
  description longtext NOT NULL,
  completed_items longtext,
  next_steps longtext,
  created_at datetime(6) NOT NULL,
  updated_at datetime(6) NOT NULL,
  created_by_id int NOT NULL,
  mentorship_id bigint NOT NULL,
  PRIMARY KEY (id),
  KEY mentorship_mentorshi_created_by_id_0ec1efef_fk_auth_user (created_by_id),
  KEY mentorship_mentorshi_mentorship_id_f84db681_fk_accounts_ (mentorship_id),
  CONSTRAINT mentorship_mentorshi_created_by_id_0ec1efef_fk_auth_user FOREIGN KEY (created_by_id) REFERENCES auth_user (id),
  CONSTRAINT mentorship_mentorshi_mentorship_id_f84db681_fk_accounts_ FOREIGN KEY (mentorship_id) REFERENCES accounts_mentorshiprequest (id)
)  
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table mentorship_mentorshipskillprogress
--

DROP TABLE IF EXISTS mentorship_mentorshipskillprogress;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE mentorship_mentorshipskillprogress (
  id bigint NOT NULL ,
  skill_name varchar(100) NOT NULL,
  initial_proficiency int NOT NULL,
  current_proficiency int NOT NULL,
  target_proficiency int NOT NULL,
  notes longtext NOT NULL,
  last_assessment_date date NOT NULL,
  created_at datetime(6) NOT NULL,
  mentorship_id bigint NOT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY mentorship_mentorshipski_mentorship_id_skill_name_1964da1c_uniq (mentorship_id,skill_name),
  CONSTRAINT mentorship_mentorshi_mentorship_id_a4f20164_fk_accounts_ FOREIGN KEY (mentorship_id) REFERENCES accounts_mentorshiprequest (id)
)  
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table mentorship_message
--

DROP TABLE IF EXISTS mentorship_message;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE mentorship_message (
  id bigint NOT NULL ,
  content longtext NOT NULL,
  attachment varchar(100) DEFAULT NULL,
  is_read tinyint(1) NOT NULL,
  created_at datetime(6) NOT NULL,
  conversation_id bigint NOT NULL,
  sender_id int NOT NULL,
  PRIMARY KEY (id),
  KEY mentorship_message_conversation_id_4c3f78e7_fk_mentorshi (conversation_id),
  KEY mentorship_message_sender_id_a27f4846_fk_auth_user_id (sender_id),
  CONSTRAINT mentorship_message_conversation_id_4c3f78e7_fk_mentorshi FOREIGN KEY (conversation_id) REFERENCES mentorship_conversation (id),
  CONSTRAINT mentorship_message_sender_id_a27f4846_fk_auth_user_id FOREIGN KEY (sender_id) REFERENCES auth_user (id)
)  
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table mentorship_timelinemilestone
--

DROP TABLE IF EXISTS mentorship_timelinemilestone;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE mentorship_timelinemilestone (
  id bigint NOT NULL ,
  period varchar(50) NOT NULL,
  description varchar(500) NOT NULL,
  status varchar(20) NOT NULL,
  created_at datetime(6) NOT NULL,
  updated_at datetime(6) NOT NULL,
  mentorship_id bigint NOT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY mentorship_timelinemiles_mentorship_id_period_des_b4004e99_uniq (mentorship_id,period,description),
  CONSTRAINT mentorship_timelinem_mentorship_id_2f6bc359_fk_accounts_ FOREIGN KEY (mentorship_id) REFERENCES accounts_mentorshiprequest (id)
)  
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table notifications_notification
--

DROP TABLE IF EXISTS notifications_notification;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE notifications_notification (
  id int NOT NULL ,
  level varchar(20) NOT NULL,
  unread tinyint(1) NOT NULL,
  actor_object_id varchar(255) NOT NULL,
  verb varchar(255) NOT NULL,
  description longtext,
  target_object_id varchar(255) DEFAULT NULL,
  action_object_object_id varchar(255) DEFAULT NULL,
  timestamp datetime(6) NOT NULL,
  public tinyint(1) NOT NULL,
  action_object_content_type_id int DEFAULT NULL,
  actor_content_type_id int NOT NULL,
  recipient_id int NOT NULL,
  target_content_type_id int DEFAULT NULL,
  deleted tinyint(1) NOT NULL,
  emailed tinyint(1) NOT NULL,
  data longtext,
  PRIMARY KEY (id),
  KEY notifications_notifi_action_object_conten_7d2b8ee9_fk_django_co (action_object_content_type_id),
  KEY notifications_notifi_actor_content_type_i_0c69d7b7_fk_django_co (actor_content_type_id),
  KEY notifications_notifi_target_content_type__ccb24d88_fk_django_co (target_content_type_id),
  KEY notifications_notification_deleted_b32b69e6 (deleted),
  KEY notifications_notification_emailed_23a5ad81 (emailed),
  KEY notifications_notification_public_1bc30b1c (public),
  KEY notifications_notification_unread_cce4be30 (unread),
  KEY notifications_notification_timestamp_6a797bad (timestamp),
  KEY notifications_notification_recipient_id_unread_253aadc9_idx (recipient_id,unread),
  CONSTRAINT notifications_notifi_action_object_conten_7d2b8ee9_fk_django_co FOREIGN KEY (action_object_content_type_id) REFERENCES django_content_type (id),
  CONSTRAINT notifications_notifi_actor_content_type_i_0c69d7b7_fk_django_co FOREIGN KEY (actor_content_type_id) REFERENCES django_content_type (id),
  CONSTRAINT notifications_notifi_target_content_type__ccb24d88_fk_django_co FOREIGN KEY (target_content_type_id) REFERENCES django_content_type (id),
  CONSTRAINT notifications_notification_recipient_id_d055f3f0_fk_auth_user_id FOREIGN KEY (recipient_id) REFERENCES auth_user (id)
)  
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table setup_setupstate
--

DROP TABLE IF EXISTS setup_setupstate;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE setup_setupstate (
  id bigint NOT NULL ,
  is_complete tinyint(1) NOT NULL,
  completed_at datetime(6) DEFAULT NULL,
  setup_data json NOT NULL,
  created_at datetime(6) NOT NULL,
  updated_at datetime(6) NOT NULL,
  PRIMARY KEY (id)
)   
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table socialaccount_socialaccount
--

DROP TABLE IF EXISTS socialaccount_socialaccount;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE socialaccount_socialaccount (
  id int NOT NULL ,
  provider varchar(200) NOT NULL,
  uid varchar(191) NOT NULL,
  last_login datetime(6) NOT NULL,
  date_joined datetime(6) NOT NULL,
  extra_data json NOT NULL,
  user_id int NOT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY socialaccount_socialaccount_provider_uid_fc810c6e_uniq (provider,uid),
  KEY socialaccount_socialaccount_user_id_8146e70c_fk_auth_user_id (user_id),
  CONSTRAINT socialaccount_socialaccount_user_id_8146e70c_fk_auth_user_id FOREIGN KEY (user_id) REFERENCES auth_user (id)
)   
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table socialaccount_socialapp
--

DROP TABLE IF EXISTS socialaccount_socialapp;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE socialaccount_socialapp (
  id int NOT NULL ,
  provider varchar(30) NOT NULL,
  name varchar(40) NOT NULL,
  client_id varchar(191) NOT NULL,
  secret varchar(191) NOT NULL,
  key varchar(191) NOT NULL,
  provider_id varchar(200) NOT NULL,
  settings json NOT NULL DEFAULT (_utf8mb4'{}'),
  PRIMARY KEY (id)
)   
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table socialaccount_socialapp_sites
--

DROP TABLE IF EXISTS socialaccount_socialapp_sites;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE socialaccount_socialapp_sites (
  id bigint NOT NULL ,
  socialapp_id int NOT NULL,
  site_id int NOT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY socialaccount_socialapp_sites_socialapp_id_site_id_71a9a768_uniq (socialapp_id,site_id),
  KEY socialaccount_socialapp_sites_site_id_2579dee5_fk_django_site_id (site_id),
  CONSTRAINT socialaccount_social_socialapp_id_97fb6e7d_fk_socialacc FOREIGN KEY (socialapp_id) REFERENCES socialaccount_socialapp (id),
  CONSTRAINT socialaccount_socialapp_sites_site_id_2579dee5_fk_django_site_id FOREIGN KEY (site_id) REFERENCES django_site (id)
)   
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table socialaccount_socialtoken
--

DROP TABLE IF EXISTS socialaccount_socialtoken;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE socialaccount_socialtoken (
  id int NOT NULL ,
  token longtext NOT NULL,
  token_secret longtext NOT NULL,
  expires_at datetime(6) DEFAULT NULL,
  account_id int NOT NULL,
  app_id int DEFAULT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY socialaccount_socialtoken_app_id_account_id_fca4e0ac_uniq (app_id,account_id),
  KEY socialaccount_social_account_id_951f210e_fk_socialacc (account_id),
  CONSTRAINT socialaccount_social_account_id_951f210e_fk_socialacc FOREIGN KEY (account_id) REFERENCES socialaccount_socialaccount (id),
  CONSTRAINT socialaccount_social_app_id_636a42d7_fk_socialacc FOREIGN KEY (app_id) REFERENCES socialaccount_socialapp (id)
)   
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table surveys_achievement
--

DROP TABLE IF EXISTS surveys_achievement;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE surveys_achievement (
  id bigint NOT NULL ,
  title varchar(200) NOT NULL,
  description longtext NOT NULL,
  achievement_date date NOT NULL,
  achievement_type varchar(20) NOT NULL,
  verified tinyint(1) NOT NULL,
  verification_date datetime(6) DEFAULT NULL,
  alumni_id bigint NOT NULL,
  verified_by_id int DEFAULT NULL,
  PRIMARY KEY (id),
  KEY surveys_achievement_alumni_id_e21ca943_fk_alumni_di (alumni_id),
  KEY surveys_achievement_verified_by_id_007544bf_fk_auth_user_id (verified_by_id),
  CONSTRAINT surveys_achievement_alumni_id_e21ca943_fk_alumni_di FOREIGN KEY (alumni_id) REFERENCES alumni_directory_alumni (id),
  CONSTRAINT surveys_achievement_verified_by_id_007544bf_fk_auth_user_id FOREIGN KEY (verified_by_id) REFERENCES auth_user (id)
)  
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table surveys_employmentrecord
--

DROP TABLE IF EXISTS surveys_employmentrecord;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE surveys_employmentrecord (
  id bigint NOT NULL ,
  company_name varchar(200) NOT NULL,
  job_title varchar(200) NOT NULL,
  industry varchar(100) NOT NULL,
  start_date date NOT NULL,
  end_date date DEFAULT NULL,
  salary_range varchar(20) DEFAULT NULL,
  alumni_id bigint NOT NULL,
  location_id bigint DEFAULT NULL,
  PRIMARY KEY (id),
  KEY surveys_employmentre_alumni_id_982a6fe4_fk_alumni_di (alumni_id),
  KEY surveys_employmentrecord_location_id_3e34ab68_fk_core_address_id (location_id),
  CONSTRAINT surveys_employmentre_alumni_id_982a6fe4_fk_alumni_di FOREIGN KEY (alumni_id) REFERENCES alumni_directory_alumni (id),
  CONSTRAINT surveys_employmentrecord_location_id_3e34ab68_fk_core_address_id FOREIGN KEY (location_id) REFERENCES core_address (id)
)  
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table surveys_questionoption
--

DROP TABLE IF EXISTS surveys_questionoption;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE surveys_questionoption (
  id bigint NOT NULL ,
  option_text varchar(200) NOT NULL,
  display_order int NOT NULL,
  allow_custom tinyint(1) NOT NULL,
  question_id bigint NOT NULL,
  PRIMARY KEY (id),
  KEY surveys_questionopti_question_id_688ddc7f_fk_surveys_s (question_id),
  CONSTRAINT surveys_questionopti_question_id_688ddc7f_fk_surveys_s FOREIGN KEY (question_id) REFERENCES surveys_surveyquestion (id)
)  
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table surveys_report
--

DROP TABLE IF EXISTS surveys_report;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE surveys_report (
  id bigint NOT NULL ,
  title varchar(200) NOT NULL,
  description longtext NOT NULL,
  report_type varchar(20) NOT NULL,
  parameters json NOT NULL,
  created_at datetime(6) NOT NULL,
  last_run datetime(6) DEFAULT NULL,
  created_by_id int NOT NULL,
  is_scheduled tinyint(1) NOT NULL,
  last_scheduled_run datetime(6) DEFAULT NULL,
  next_scheduled_run datetime(6) DEFAULT NULL,
  schedule_frequency varchar(20) NOT NULL,
  PRIMARY KEY (id),
  KEY surveys_report_created_by_id_da202bc5_fk_auth_user_id (created_by_id),
  CONSTRAINT surveys_report_created_by_id_da202bc5_fk_auth_user_id FOREIGN KEY (created_by_id) REFERENCES auth_user (id)
)  
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table surveys_responseanswer
--

DROP TABLE IF EXISTS surveys_responseanswer;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE surveys_responseanswer (
  id bigint NOT NULL ,
  text_answer longtext,
  rating_value int DEFAULT NULL,
  selected_option_id bigint DEFAULT NULL,
  question_id bigint NOT NULL,
  response_id bigint NOT NULL,
  PRIMARY KEY (id),
  KEY surveys_responseansw_selected_option_id_dd3ab198_fk_surveys_q (selected_option_id),
  KEY surveys_responseansw_question_id_ac302736_fk_surveys_s (question_id),
  KEY surveys_responseansw_response_id_050ef226_fk_surveys_s (response_id),
  CONSTRAINT surveys_responseansw_question_id_ac302736_fk_surveys_s FOREIGN KEY (question_id) REFERENCES surveys_surveyquestion (id),
  CONSTRAINT surveys_responseansw_response_id_050ef226_fk_surveys_s FOREIGN KEY (response_id) REFERENCES surveys_surveyresponse (id),
  CONSTRAINT surveys_responseansw_selected_option_id_dd3ab198_fk_surveys_q FOREIGN KEY (selected_option_id) REFERENCES surveys_questionoption (id)
)   
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table surveys_survey
--

DROP TABLE IF EXISTS surveys_survey;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE surveys_survey (
  id bigint NOT NULL ,
  title varchar(200) NOT NULL,
  description longtext NOT NULL,
  created_at datetime(6) NOT NULL,
  start_date datetime(6) NOT NULL,
  end_date datetime(6) NOT NULL,
  status varchar(10) NOT NULL,
  is_external tinyint(1) NOT NULL,
  external_url varchar(200) DEFAULT NULL,
  created_by_id int NOT NULL,
  PRIMARY KEY (id),
  KEY surveys_survey_created_by_id_46a3da67_fk_auth_user_id (created_by_id),
  CONSTRAINT surveys_survey_created_by_id_46a3da67_fk_auth_user_id FOREIGN KEY (created_by_id) REFERENCES auth_user (id)
)   
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table surveys_surveyquestion
--

DROP TABLE IF EXISTS surveys_surveyquestion;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE surveys_surveyquestion (
  id bigint NOT NULL ,
  question_text longtext NOT NULL,
  question_type varchar(20) NOT NULL,
  is_required tinyint(1) NOT NULL,
  help_text longtext NOT NULL,
  display_order int NOT NULL,
  scale_type varchar(20) DEFAULT NULL,
  survey_id bigint NOT NULL,
  PRIMARY KEY (id),
  KEY surveys_surveyquestion_survey_id_ca0121e7_fk_surveys_survey_id (survey_id),
  CONSTRAINT surveys_surveyquestion_survey_id_ca0121e7_fk_surveys_survey_id FOREIGN KEY (survey_id) REFERENCES surveys_survey (id)
)   
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table surveys_surveyresponse
--

DROP TABLE IF EXISTS surveys_surveyresponse;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE surveys_surveyresponse (
  id bigint NOT NULL ,
  submitted_at datetime(6) NOT NULL,
  ip_address char(39) DEFAULT NULL,
  alumni_id bigint NOT NULL,
  survey_id bigint NOT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY surveys_surveyresponse_survey_id_alumni_id_7f402500_uniq (survey_id,alumni_id),
  KEY surveys_surveyrespon_alumni_id_d9f84010_fk_alumni_di (alumni_id),
  CONSTRAINT surveys_surveyrespon_alumni_id_d9f84010_fk_alumni_di FOREIGN KEY (alumni_id) REFERENCES alumni_directory_alumni (id),
  CONSTRAINT surveys_surveyresponse_survey_id_4ad3a956_fk_surveys_survey_id FOREIGN KEY (survey_id) REFERENCES surveys_survey (id)
)   
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table taggit_tag
--

DROP TABLE IF EXISTS taggit_tag;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE taggit_tag (
  id int NOT NULL ,
  name varchar(100) NOT NULL,
  slug varchar(100) NOT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY name (name),
  UNIQUE KEY slug (slug)
)   
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table taggit_taggeditem
--

DROP TABLE IF EXISTS taggit_taggeditem;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE taggit_taggeditem (
  id int NOT NULL ,
  object_id int NOT NULL,
  content_type_id int NOT NULL,
  tag_id int NOT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY taggit_taggeditem_content_type_id_object_id_tag_id_4bb97a8e_uniq (content_type_id,object_id,tag_id),
  KEY taggit_taggeditem_tag_id_f4f5b767_fk_taggit_tag_id (tag_id),
  KEY taggit_taggeditem_object_id_e2d7d1df (object_id),
  KEY taggit_tagg_content_8fc721_idx (content_type_id,object_id),
  CONSTRAINT taggit_taggeditem_content_type_id_9957a03c_fk_django_co FOREIGN KEY (content_type_id) REFERENCES django_content_type (id),
  CONSTRAINT taggit_taggeditem_tag_id_f4f5b767_fk_taggit_tag_id FOREIGN KEY (tag_id) REFERENCES taggit_tag (id)
)   
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-03-06 21:48:14
