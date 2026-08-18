<?php
/**
 * Plugin Name: NOVAIQ Connector
 * Description: NOVAIQ 自動投稿ツール用のカスタムRESTエンドポイント。標準の
 *   Authorization ヘッダを落とすホスト（ConoHa WING 等）でも動くよう、独自ヘッダ
 *   X-NOVAIQ-KEY で認証します。wp-content/mu-plugins/ に置くと自動有効化されます。
 * Version: 0.2.0
 */

if (!defined('ABSPATH')) {
    exit;
}

/*
 * === 設定 ===
 * 下の 'CHANGE_ME_TO_A_LONG_RANDOM_STRING' を、長いランダムな文字列に変更してください。
 * そして、同じ値を NOVAIQ ツール側の Secrets の NOVAIQ_API_KEY に登録します。
 * （wp-config.php に define('NOVAIQ_API_KEY', '...') を書けばそちらが優先されます）
 */
if (!defined('NOVAIQ_API_KEY')) {
    define('NOVAIQ_API_KEY', 'CHANGE_ME_TO_A_LONG_RANDOM_STRING');
}

add_action('rest_api_init', function () {
    register_rest_route('novaiq/v1', '/ping', array(
        'methods'             => 'GET',
        'callback'            => 'novaiq_ping',
        'permission_callback' => 'novaiq_check_key',
    ));
    register_rest_route('novaiq/v1', '/post', array(
        'methods'             => 'POST',
        'callback'            => 'novaiq_create_post',
        'permission_callback' => 'novaiq_check_key',
    ));
    // Read a post's RAW content (shortcodes intact) by id — used to import
    // existing AFFINGER decoration samples.
    register_rest_route('novaiq/v1', '/get', array(
        'methods'             => 'GET',
        'callback'            => 'novaiq_get_post',
        'permission_callback' => 'novaiq_check_key',
    ));
    register_rest_route('novaiq/v1', '/update', array(
        'methods'             => 'POST',
        'callback'            => 'novaiq_update_post',
        'permission_callback' => 'novaiq_check_key',
    ));
});

function novaiq_get_post(WP_REST_Request $req) {
    $id = (int) $req->get_param('id');
    if (!$id) {
        return new WP_Error('novaiq_bad_request', 'id required', array('status' => 400));
    }
    $post = get_post($id);
    if (!$post) {
        return new WP_Error('novaiq_not_found', 'post not found', array('status' => 404));
    }
    return array(
        'ok'          => true,
        'id'          => $post->ID,
        'title'       => $post->post_title,
        'status'      => $post->post_status,
        'raw_content' => $post->post_content, // unfiltered: shortcodes preserved
    );
}

function novaiq_get_key_header() {
    if (isset($_SERVER['HTTP_X_NOVAIQ_KEY'])) {
        return trim($_SERVER['HTTP_X_NOVAIQ_KEY']);
    }
    return '';
}

function novaiq_check_key() {
    $provided = novaiq_get_key_header();
    if (!$provided || !hash_equals(NOVAIQ_API_KEY, $provided)) {
        return new WP_Error('novaiq_forbidden', 'Invalid NOVAIQ key', array('status' => 401));
    }
    return true;
}

function novaiq_admin_id() {
    $admins = get_users(array('role' => 'administrator', 'number' => 1, 'orderby' => 'ID', 'order' => 'ASC'));
    return $admins ? (int) $admins[0]->ID : 0;
}

function novaiq_ping() {
    $admins = get_users(array('role' => 'administrator', 'number' => 1, 'orderby' => 'ID', 'order' => 'ASC'));
    return array(
        'ok'    => true,
        'site'  => get_bloginfo('name'),
        'admin' => $admins ? $admins[0]->display_name : '',
        'wp'    => get_bloginfo('version'),
    );
}

// REST-safe category resolver (wp_create_category/get_cat_ID are wp-admin only).
function novaiq_resolve_category_ids($names) {
    $ids = array();
    foreach ((array) $names as $cname) {
        $cname = sanitize_text_field($cname);
        if ($cname === '') {
            continue;
        }
        $term = term_exists($cname, 'category');
        if (!$term) {
            $term = wp_insert_term($cname, 'category');
        }
        if (!is_wp_error($term) && isset($term['term_id'])) {
            $ids[] = (int) $term['term_id'];
        }
    }
    return $ids;
}

function novaiq_attach_featured_image($post_id, $fname, $b64, &$warnings) {
    try {
        $bytes = base64_decode($b64);
        if ($bytes === false) {
            $warnings[] = 'image base64 decode failed';
            return;
        }

        $upload = wp_upload_bits($fname, null, $bytes);
        if (!empty($upload['error'])) {
            $warnings[] = 'upload: ' . $upload['error'];
            return;
        }

        $filetype  = wp_check_filetype($upload['file']);
        $mime      = !empty($filetype['type']) ? $filetype['type'] : 'image/png';
        $attach_id = wp_insert_attachment(array(
            'post_mime_type' => $mime,
            'post_title'     => sanitize_file_name(pathinfo($fname, PATHINFO_FILENAME)),
            'post_content'   => '',
            'post_status'    => 'inherit',
        ), $upload['file'], $post_id);
        if (is_wp_error($attach_id)) {
            $warnings[] = 'attachment: ' . $attach_id->get_error_message();
            return;
        }

        // Set the featured image first — this does not require metadata/GD.
        set_post_thumbnail($post_id, $attach_id);

        // Best-effort metadata (thumbnails). Never let this abort the request.
        try {
            require_once ABSPATH . 'wp-admin/includes/image.php';
            if (function_exists('wp_generate_attachment_metadata')) {
                $meta = wp_generate_attachment_metadata($attach_id, $upload['file']);
                if (!empty($meta)) {
                    wp_update_attachment_metadata($attach_id, $meta);
                }
            }
        } catch (\Throwable $e) {
            $warnings[] = 'metadata: ' . $e->getMessage();
            $size = @getimagesize($upload['file']);
            if ($size) {
                wp_update_attachment_metadata($attach_id, array(
                    'width'  => $size[0],
                    'height' => $size[1],
                    'file'   => $upload['file'],
                ));
            }
        }
    } catch (\Throwable $e) {
        $warnings[] = 'image: ' . $e->getMessage();
    }
}

function novaiq_create_post(WP_REST_Request $req) {
    try {
        $p = $req->get_json_params();
        if (!$p) {
            $p = $req->get_params();
        }

        $title   = isset($p['title']) ? wp_strip_all_tags($p['title']) : '';
        $content = isset($p['content']) ? $p['content'] : '';
        $slug    = isset($p['slug']) ? sanitize_title($p['slug']) : '';
        $status  = isset($p['status']) ? $p['status'] : 'draft';
        $allowed = array('draft', 'pending', 'publish', 'future');
        if (!in_array($status, $allowed, true)) {
            $status = 'draft';
        }

        if ($title === '' || $content === '') {
            return new WP_Error('novaiq_bad_request', 'title and content are required', array('status' => 400));
        }

        $postarr = array(
            'post_title'   => $title,
            'post_content' => wp_kses_post($content),
            'post_status'  => $status,
            'post_type'    => 'post',
            'post_author'  => novaiq_admin_id(),
        );
        if ($slug) {
            $postarr['post_name'] = $slug;
        }
        if (!empty($p['categories']) && is_array($p['categories'])) {
            $cat_ids = novaiq_resolve_category_ids($p['categories']);
            if ($cat_ids) {
                $postarr['post_category'] = $cat_ids;
            }
        }

        $post_id = wp_insert_post($postarr, true);
        if (is_wp_error($post_id)) {
            return new WP_Error('novaiq_insert_failed', $post_id->get_error_message(), array('status' => 500));
        }

        $warnings = array();

        if (!empty($p['tags']) && is_array($p['tags'])) {
            wp_set_post_tags($post_id, array_map('sanitize_text_field', $p['tags']), false);
        }

        if (!empty($p['image_base64'])) {
            $fname = !empty($p['image_filename']) ? sanitize_file_name($p['image_filename']) : 'eyecatch.png';
            novaiq_attach_featured_image($post_id, $fname, $p['image_base64'], $warnings);
        }

        return array(
            'ok'        => true,
            'id'        => $post_id,
            'status'    => $status,
            'edit_link' => admin_url('post.php?post=' . $post_id . '&action=edit'),
            'warnings'  => $warnings,
        );
    } catch (\Throwable $e) {
        // Surface the real error instead of a generic 500 page (aids debugging).
        return new WP_Error('novaiq_exception', $e->getMessage(), array('status' => 500));
    }
}

function novaiq_update_post(WP_REST_Request $req) {
    try {
        $p = $req->get_json_params();
        if (!$p) {
            $p = $req->get_params();
        }

        $id = isset($p['id']) ? (int) $p['id'] : 0;
        if (!$id) {
            return new WP_Error('novaiq_bad_request', 'id required', array('status' => 400));
        }
        $existing = get_post($id);
        if (!$existing || $existing->post_type !== 'post') {
            return new WP_Error('novaiq_not_found', 'post not found', array('status' => 404));
        }

        $postarr = array('ID' => $id);
        if (isset($p['title']) && $p['title'] !== '') {
            $postarr['post_title'] = wp_strip_all_tags($p['title']);
        }
        if (isset($p['content']) && $p['content'] !== '') {
            $postarr['post_content'] = wp_kses_post($p['content']);
        }
        if (!empty($p['slug'])) {
            $postarr['post_name'] = sanitize_title($p['slug']);
        }
        if (!empty($p['status'])) {
            $allowed = array('draft', 'pending', 'publish', 'future');
            if (in_array($p['status'], $allowed, true)) {
                $postarr['post_status'] = $p['status'];
            }
        }
        if (!empty($p['categories']) && is_array($p['categories'])) {
            $cat_ids = novaiq_resolve_category_ids($p['categories']);
            if ($cat_ids) {
                $postarr['post_category'] = $cat_ids;
            }
        }

        $updated = wp_update_post($postarr, true);
        if (is_wp_error($updated)) {
            return new WP_Error('novaiq_update_failed', $updated->get_error_message(), array('status' => 500));
        }

        $warnings = array();
        if (!empty($p['tags']) && is_array($p['tags'])) {
            wp_set_post_tags($id, array_map('sanitize_text_field', $p['tags']), false);
        }
        if (!empty($p['image_base64'])) {
            $fname = !empty($p['image_filename']) ? sanitize_file_name($p['image_filename']) : 'eyecatch.png';
            novaiq_attach_featured_image($id, $fname, $p['image_base64'], $warnings);
        }

        return array(
            'ok'        => true,
            'id'        => $id,
            'status'    => get_post_status($id),
            'edit_link' => admin_url('post.php?post=' . $id . '&action=edit'),
            'warnings'  => $warnings,
        );
    } catch (\Throwable $e) {
        return new WP_Error('novaiq_exception', $e->getMessage(), array('status' => 500));
    }
}
