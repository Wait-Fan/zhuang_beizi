CREATE DATABASE IF NOT EXISTS `zhuangdb` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE `zhuangdb`;

CREATE TABLE IF NOT EXISTS `wcs_stock_box`  (
  `id` bigint UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键',
  `box_spec` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '箱子规格 (length,width,height,box_type)',
  `case_type` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT '' COMMENT '托盘型号 case_type',
  `target_num` int NULL DEFAULT 1 COMMENT '数量 target_num',
  `order_id` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT '' COMMENT '订单号 order_id',
  `case_group` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT '0' COMMENT '拼箱组号 case_group',
  `product_code` bigint NOT NULL COMMENT '产品编码 product_code（一箱一码，唯一）',
  `priority` int NULL DEFAULT 0 COMMENT '优先级 priority',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_product_code`(`product_code`) USING BTREE,
  INDEX `idx_order_id`(`order_id`) USING BTREE,
  INDEX `idx_case_type`(`case_type`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = 'WCS当前立库快照' ROW_FORMAT = Dynamic;

CREATE TABLE IF NOT EXISTS `wcs_stock_box_all`  (
  `id` bigint UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键',
  `box_spec` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '箱子规格 (length,width,height,box_type)',
  `case_type` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT '' COMMENT '托盘型号 case_type',
  `target_num` int NULL DEFAULT 1 COMMENT '数量 target_num',
  `order_id` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT '' COMMENT '订单号 order_id',
  `case_group` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT '0' COMMENT '拼箱组号 case_group',
  `product_code` bigint NOT NULL COMMENT '产品编码 product_code（一箱一码，唯一）',
  `priority` int NULL DEFAULT 0 COMMENT '优先级 priority',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_product_code`(`product_code`) USING BTREE,
  INDEX `idx_order_id`(`order_id`) USING BTREE,
  INDEX `idx_case_type`(`case_type`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = 'WCS接口库存箱子（由接口1 JSON 落库）' ROW_FORMAT = Dynamic;

CREATE TABLE IF NOT EXISTS `wcs_success_box`  (
  `id` bigint UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键，自增',
  `box_unique_id` char(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '托盘方案唯一ID（一盘多箱相同，对方按此查询）',
  `seq` int UNSIGNED NOT NULL COMMENT '盘内执行序号（从1开始）',
  `raw_length` double NOT NULL COMMENT '箱子真实长度 mm',
  `raw_width` double NOT NULL COMMENT '箱子真实宽度 mm',
  `raw_height` double NOT NULL COMMENT '箱子真实高度 mm',
  `pos_x` double NOT NULL COMMENT '放置坐标 x mm',
  `pos_y` double NOT NULL COMMENT '放置坐标 y mm',
  `pos_z` double NOT NULL COMMENT '放置坐标 z mm',
  `stack_height_before` double NOT NULL DEFAULT 0 COMMENT '放置当前箱之前的垛型最高顶面 mm',
  `state` tinyint UNSIGNED NULL DEFAULT NULL COMMENT '朝向：初始空；接口4后写1=不转/2=转90°',
  `pallet_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '算法内部托盘编号（可选，便于人对账）',
  `order_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '销售订单号 sales_order_no',
  `case_type` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '托盘类型 pallet_type，如 MH423C',
  `created_at` datetime(0) NOT NULL DEFAULT CURRENT_TIMESTAMP(0) COMMENT '写入时间',
  `product_code` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '箱子唯一编号',
  `is_send` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '是否下传\r\n1：已下传\r\n2：未下传',
  `case_group` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL,
  `camera_length` double NULL DEFAULT NULL,
  `camera_width` double NULL DEFAULT NULL,
  `camera_height` double NULL DEFAULT NULL,
  `box_num` int NULL DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_box_unique_seq`(`box_unique_id`, `seq`) USING BTREE,
  INDEX `idx_box_unique_id`(`box_unique_id`) USING BTREE,
  INDEX `idx_created_at`(`created_at`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '达标托盘箱子明细：每次计算结束后有达标盘则按箱插入' ROW_FORMAT = Dynamic;

CREATE TABLE IF NOT EXISTS `wcs_box_orientation`  (
  `id` bigint UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键，自增',
  `box_unique_id` char(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '托盘方案唯一ID',
  `seq` int UNSIGNED NOT NULL COMMENT '盘内执行序号（从1开始）',
  `item_id` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '计划内箱子 id，绑相机 box_id',
  `product_code` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '库存/内部 product_code（可选）',
  `suction_orientation` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '如 cup_600x_800y / cup_800x_600y',
  `suction_cup_x_size` double NULL DEFAULT NULL COMMENT '吸盘 X 尺寸 mm',
  `suction_cup_y_size` double NULL DEFAULT NULL COMMENT '吸盘 Y 尺寸 mm',
  `target_orientation_deg` tinyint UNSIGNED NOT NULL COMMENT '目标姿态：0 或 90',
  `created_at` datetime(0) NOT NULL DEFAULT CURRENT_TIMESTAMP(0) COMMENT '写入时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_orient_unique_seq`(`box_unique_id`, `seq`) USING BTREE,
  INDEX `idx_orient_item_id`(`item_id`) USING BTREE,
  INDEX `idx_orient_created_at`(`created_at`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '每箱目标姿态：接口4到达后与相机角比较，更新 wcs_success_box.state' ROW_FORMAT = Dynamic;

CREATE TABLE IF NOT EXISTS `wcs_plc_queue`  (
  `id` bigint UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键',
  `box_unique_id` char(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '托盘方案唯一ID',
  `seq` int UNSIGNED NOT NULL COMMENT '盘内序号',
  `product_code` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '箱子编号（展示用）',
  `item_id` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '计划内箱子 id',
  `state` tinyint UNSIGNED NOT NULL COMMENT '旋转状态 1/2（写入命令时快照）',
  `target_orientation_deg` tinyint UNSIGNED NULL DEFAULT NULL COMMENT '目标姿态 0/90',
  `camera_orientation_deg` tinyint UNSIGNED NULL DEFAULT NULL COMMENT '相机姿态 0/90',
  `command_json` json NOT NULL COMMENT '已构造的 DB19 字段',
  `status` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'pending' COMMENT 'pending/sent/failed',
  `send_note` varchar(512) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '发送结果说明',
  `created_at` datetime(0) NOT NULL DEFAULT CURRENT_TIMESTAMP(0),
  `sent_at` datetime(0) NULL DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_plc_unique_seq`(`box_unique_id`, `seq`) USING BTREE,
  INDEX `idx_plc_status_created`(`status`, `created_at`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = 'PLC 命令队列：state 就绪后自动入队下传；界面可应急补发' ROW_FORMAT = Dynamic;
