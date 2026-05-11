# Qencode Transcoding API — Schema Digest

_Generated from `src/data/api/transcoding.json` (source sha256 prefix `a6c957f39f5c`). Do not edit by hand — run `scripts/build_assets.py`._

Endpoints (in call order):

- [`POST /v1/access_token`](#access_token) — Qencode requires an api_key to generate a session-based token to authenticate requests and launch tasks. You can view an…
- [`POST /v1/create_task`](#create_task) — Once you have received your token , use the /v1/create_task method to receive the task_token , which is used to define y…
- [`POST /v1/start_encode2`](#start_encode2) — Starts a transcoding job that contains all the parameters needed to transcode your videos into the formats, codecs, reso…
- [`POST /v1/status`](#status) — Gets the current status of one or more transcoding jobs. The https://api.qencode.com/v1/status endpoint is a quick way t…
- [`OPTIONS, POST, PATCH /v1/upload_file`](#upload_file) — Provides endpoint for direct video file upload using the TUS protocol for resumable uploads. Endpoint URL is returned wi…

---

## `POST /v1/access_token` <a id="access_token"></a>

Qencode requires an api_key to generate a session-based token to authenticate requests and launch tasks. You can view and manage the API keys associated with your Projects inside of your Qencode Account . To get started, use the /v1/access_token method to acquire the session-based token , which you will use to authenticate all other requests through the Qencode API.

**Arguments:**

| Name | Type | Req | Description |
|---|---|---|---|
| `api_key` | string | yes | The API key of a Project used to authenticate access to create tasks. |


**Returns:**

| Name | Type | Req | Description |
|---|---|---|---|
| `token` | — | no | The session token received after API accesss is authenticated. |


---

## `POST /v1/create_task` <a id="create_task"></a>

Once you have received your token , use the /v1/create_task method to receive the task_token , which is used to define your transcoding parameters in the next step. You will also receive an upload_url which can be used for direct uploads via the /v1/upload_file method.

**Arguments:**

| Name | Type | Req | Description |
|---|---|---|---|
| `token` | string | yes | The token from the /v1/access_token method, used to create a task. |


**Returns:**

| Name | Type | Req | Description |
|---|---|---|---|
| `task_token` | — | no | The token used for starting a transcoding task using the /v1/start_encode2 method below. |
| `upload_url` | — | no | The endpoint used for the direct upload of source videos. |


---

## `POST /v1/start_encode2` <a id="start_encode2"></a>

Starts a transcoding job that contains all the parameters needed to transcode your videos into the formats, codecs, resolutions you need, along with the list of fully customizable settings. Pass the task_token with the /v1/start_encode2 method, along with the query JSON object containg the request with your transcoding parameters. You can also include the payload parameter to send additional data with the task that can be retireved in the future. The source parameter within the query JSON object can also be used for uploads by specifying 'tus:<file_uuid>'. You can also use the stitch parameter to stitch multiple videos together into one See Tutorial for Stitching Videos .

**Arguments:**

| Name | Type | Req | Description |
|---|---|---|---|
| `task_token` | string | yes | The token used for starting a transcoding task received from the /v1/create_task method above. |
| `query` | json | yes | A JSON object containing the API request with transcoding parameters. See query object structure . |
| `payload` | string | no | Additional data sent with a task, which can be retrieved in the future. |


### `start_encode2.query`  
_type: json_

A JSON object containing the API request with transcoding parameters. See query object structure .

| Name | Type | Req | Description |
|---|---|---|---|
| `source` | string | yes | The URI of a single source video used for the input. |
| `stitch` | — | yes | The list of URIs for multiple source videos to be stitched together. |
| `format` | array of objects | yes | List of objects describing the output transcoding parameters |
| `callback_url` | string (4000 characters max) | no | An HTTP callback (Webhook URL) for event updates. |
| `use_subtask_callback` | integer (1 or 0) | no | Enables callbacks on the subtask level |
| `refresh_playlist` | integer (0 or 1) | no | Enables incremental updates for ABR playlists |
| `retry_on_error` | integer (0 or 1) | no | Retries the transcoding job if the initial job ends with an error. |
| `upscale` | integer (1 or 0) | no | Enables upscaling |
| `encoder_version` | integer (1 or 2) | no | Encoding system version |


#### `start_encode2.query.format`  
_type: array of objects_

List of objects describing the output transcoding parameters

| Name | Type | Req | Description |
|---|---|---|---|
| `output` | string | yes | The type of output to be created as part of this transcoding task. |
| `start_time` | float | no | The start time within the source audio or video file, used with duration to create shorter clips. |
| `duration` | float | no | The duration (in seconds) from the start_time , used for creating shorter audio or video clips. |
| `destination` | object or array of objects | no | Output destination |
| `size` | string (WxH) | no | Size dimensions of the output video or image frame |
| `width` | integer | no | Width of the output video or image frame |
| `height` | integer | no | Height of the output video or image frame |
| `resolution` | integer | no | Output video frame smaller dimension in pixels |
| `rotate` | integer | no | Video rotation angle |
| `aspect_ratio` | float or string | no | Output video aspect ratio |
| `resize_mode` | string ('scale' or 'crop') | no | Frame resize mode |
| `framerate` | string | no | Output video frame rate |
| `framerate_limit` | string | no | Limits the output video frame rate to a specified maximum value without altering videos that already have a lower frame rate. |
| `keyframe` | integer or string | no | Output video keyframe interval |
| `quality` | integer | no | Output video stream quality (CRF) |
| `bitrate` | integer | no | Output video stream bitrate (kbps) |
| `two_pass` | integer (1 or 0) | no | Enables two pass mode |
| `pix_format` | string | no | Output video pixel format |
| `packager_version` | integer | no | Specifies the packaging engine version to use during split to HLS or DASH. |
| `video_codec` | string | no | Output stream video codec |
| `profile` | string | no | Video codec settings profile |
| `video_codec_parameters` | object | no | Output stream video codec parameters |
| `tag_video` | string | no | Specifies tag for output video stream |
| `hdr_to_sdr` | integer (1 or 0) | no | Enables HDR to SDR conversion mode |
| `audio_codec` | string | no | Audio codec name |
| `audio_bitrate` | integer | no | Audio bitrate (kbps) |
| `audio_sample_rate` | integer | no | Audio sample rate |
| `audio_channels_number` | integer | no | Audio channels number |
| `audio_mute` | integer (0 or 1) | no | Mutes the audio in the output |
| `audio_pan` | string | no | Specifies mapping for audio channels |
| `playlist_name` | string | no | Custom master playlist filename for HLS/DASH outputs |
| `stream` | array of objects | no | List of ABR streams |
| `segment_duration` | integer | no | Segment duration (seconds) |
| `i_frames_only` | integer (1 or 0) | no | Enables #EXT-X-I-FRAMES-ONLY playlist for HLS |
| `fmp4` | integer (0 or 1) | no | Creates HLS chunks in fMp4 |
| `create_m3u8_playlist` | integer (0 or 1) | no | Creates m3u8 playlist in DASH output |
| `separate_audio` | integer (0 or 1) | no | Separates audio stream in HLS |
| `single_folder` | integer (0 or 1) | no | Puts all files of HLS output into a single folder |
| `time` | float (from 0 to 1) | no | Thumbnail time |
| `frame_number` | integer | no | Thumbnail frame number |
| `interval` | integer | no | Thumbnails interval |
| `image_format` | string | no | Thumbnail image format |
| `sprite` | integer (0 or 1) | no | Enables sprite mode for thumbnails |
| `columns` | integer | no | Specifies number of columns in a thumbnail sprite |
| `subtitles` | object | no | Closed captions configuration |
| `logo` | object or array of objects | no | Adds watermark / logo to a video output |
| `color_space` | string | no | YUV colorspace type |
| `color_range` | string | no | YUV color range |
| `color_trc` | string | no | Color transfer characteristic |
| `color_primaries` | string | no | Chromaticity coordinates of the source primaries |
| `optimize_bitrate` | integer (0 or 1) | no | Enables Per-Title Encoding mode. |
| `min_crf` | integer | no | Lowest CRF for Per-Title Encoding mode |
| `max_crf` | integer | no | Highest CRF for Per-Title Encoding mode |
| `adjust_crf` | integer | no | CRF adjustment for Per-Title Encoding mode |
| `tag` | string | no | User tag value |
| `incremental_tag` | string | no | Identifier for managing and appending resolutions in sequential transcoding jobs |
| `cenc_drm` | object | no | Widevine and Playready DRM encryption parameters |
| `fps_drm` | object | no | Fairplay DRM encryption parameters |
| `encryption` | object | no | AES-128 encryption parameters |
| `metadata_version` | string | no | FFPROBE util version |
| `audio_copy` | integer (1 or 0) | no | Copy audio stream to output |
| `video_copy` | integer (1 or 0) | no | Copy video stream to output |
| `subtitles_copy` | integer (1 or 0) | no | Copy subtitles stream to output |
| `metadata_copy` | integer (1 or 0) | no | Copy metadata stream to output |
| `deinterlace` | integer (0 or 1) | no | Forces deinterlacing of the output video stream |
| `transcript` | integer (1 or 0) | no | Save transcript for 'speech_to_text' output |
| `transcript_name` | string | no | Transcript output file name |
| `json` | integer (1 or 0) | no | Save json for 'speech_to_text' output |
| `json_name` | string | no | Timestamps JSON output file name |
| `srt` | integer (1 or 0) | no | Save substitles in SRT format for 'speech_to_text' output |
| `srt_name` | string | no | SRT subtitles output file name |
| `vtt` | integer (1 or 0) | no | Save substitles in VTT format for 'speech_to_text' output |
| `vtt_name` | string | no | VTT subtitles output file name |
| `mode` | string | no | Specifies the processing mode for 'speech_to_text' output. Options include speed, accuracy or balanced. |
| `language` | string | no | Specifies a primary language for 'speech_to_text' output using ISO 639-1 format. |
| `translate_languages` | array | no | List of target language codes (ISO 639-1) to translate the transcript into. One set of output files is generated per language. |
| `allow_soft_fail` | integer (0 or 1) | no | Allows this output to soft-fail without causing an error to the transcoding job. |
| `vmaf_model` | string | no | Specifies the model for VMAF calculation. |
| `distorted` | string | no | Distorted video URL for VMAF calculation |
| `n_subsample` | string | no | Frame subsampling value |
| `shortest` | integer (0 or 1) | no | Stop at the last frame of the shorter clip when generating vmaf output. |
| `keep_360_metadata` | integer (0 or 1) | no | Preserves 360° (spherical) video metadata in the output. |
| `inject_360_metadata` | object | no | Specifies metadata attributes for 360° or VR180 video formats, including projection type, stereoscopic mode, and optional VR180 crop geometry. |


##### `start_encode2.query.format[].destination`  
_type: object or array of objects_

Output destination

| Name | Type | Req | Description |
|---|---|---|---|
| `url` | string | yes | The URL (including the protocol) of the output to be created |
| `key` | string | yes | S3 storage Access Key ID |
| `secret` | string | yes | S3 storage Secret Access Key |
| `permissions` | string | no | S3 object access permissions |
| `storage_class` | string | no | S3 storage class (AWS) |
| `cache_control` | string | no | Sets the Cache-Control metadata for S3 storage |
| `is_passive` | integer (1 or 0) | no | Enables FTP passive mode |
| `use_tls` | integer (1 or 0) | no | Enables FTP over SSL (TLS) |
| `tcp_port` | integer | no | TCP port for Aspera |
| `udp_port` | integer | no | UDP port for Aspera |


##### `start_encode2.query.format[].video_codec_parameters`  
_type: object_

Output stream video codec parameters

| Name | Type | Req | Description |
|---|---|---|---|
| `vprofile` | string | no | Video codec settings profile |
| `level` | integer | no | Video codec level |
| `coder` | integer (1 or 0) | no | Context-Adaptive Binary Arithmetic Coding |
| `flags2` | string | no | Allows B-frames to be kept as references |
| `partitions` | string | no | One of x264's most useful features is the ability to choose among many combinations of inter and intra partitions. Possible values are +partp8x8, +partp4x4, +partb8x8, +parti8x8, +parti4x4. Defaults to None. |
| `directpred` | string | no | Defines motion detection type: 0 - none, 1 - spatial, 2 - temporal, 3 - auto. Defaults to 1. |
| `me_method` | string | no | Motion Estimation method used in encoding. Possible values are epzs, hex, umh, full. Defaults to None. |
| `subq` | string | no | Sets sub pel motion estimation quality. |
| `trellis` | string | no | Sets rate-distortion optimal quantization. |
| `refs` | string | no | Number of reference frames each P-frame can use. The range is from 0-16. |
| `cmp` | string | no | Sets full pel me compare function. |
| `me_range` | string | no | Sets limit motion vectors range (1023 for DivX player). |
| `sc_threshold` | string | no | Sets scene change threshold. |
| `i_qfactor` | string | no | Sets QP factor between P and I frames. |
| `b_strategy` | string | no | Sets strategy to choose between I/P/B-frames. |
| `qcomp` | string | no | Sets video quantizer scale compression (VBR). It is used as a constant in the ratecontrol equation. Recommended range for default rc_eq: 0.0-1.0. |
| `qmin` | string | no | Sets min video quantizer scale (VBR). Must be included between -1 and 69, default value is 2. |
| `qmax` | string | no | Sets max video quantizer scale (VBR). Must be included between -1 and 1024, default value is 31. |
| `qdiff` | string | no | Sets max difference between the quantizer scale (VBR). |
| `max_rate` | integer | no | Sets max bitrate tolerance. Requires 'bufsize' to be set. For libx264 max_rate is specified in Mbps. For other codecs - in kbps. |
| `min_rate` | integer | no | Sets min bitrate tolerance (in bits/s). Most useful in setting up a CBR encode. It is of little use elsewise. For libx264 min_rate is specified in Mbps. For other codecs - in kbps. |
| `bufsize` | integer | no | Tells the encoder how often to calculate the average bitrate and check to see if it conforms to the average bitrate specified. For libx264 bufsize is specified in Mbps. For other codecs - in kbps. |
| `sws_flags` | string | no | Sets the scaler flags. This is also used to set the scaling algorithm. Only a single algorithm should be selected. Default value is 'bicubic'. |
| `preset` | string | no | Controls the speed / compression-efficiency trade-off for the encoder |
| `flags` | string | no | Set generic flags. Possible values: mv4, qpel, loop, qscale, pass1, pass2, gray, emu_edge, psnr, truncated, ildct, low_delay, global_header, bitexact, aic, cbp, qprd, ilme, cgop. |
| `rc_lookahead` | string | no | Sets number of frames to look ahead for frametype and ratecontrol. |
| `lcevc_tune` | string | no | LCEVC tune option |
| `scaling_mode_level0` | string | no | LCEVC scaling mode |
| `dc_dithering_type` | string | no | LCEVC dithering mode |
| `dc_dithering_strength` | integer (0-10) | no | LCEVC dithering strength |
| `dc_dithering_qp_start` | integer (0-51) | no | LCEVC base QP value for dithering |
| `dc_dithering_qp_saturate` | integer (0-51) | no | LCEVC saturate QP value for dithering |
| `m_ad_mode` | string | no | LCEVC M adaptive downsampling mode |
| `m_hf_strength` | fractional (0-0.5) | no | LCEVC M high frequency strength |
| `m_lf_strength` | fractional (0-1.0) | no | LCEVC M low frequency strength |
| `tune` | integer (0, 1, 2) | no | Optimizes encoding for specific use cases such as visual quality or performance |
| `aq_mode` | integer (0, 1, 2, 3) | no | Controls adaptive quantization behavior |
| `film_grain` | integer (0, 1) | no | Enables synthetic film grain generation for visual texture |
| `fast_decode` | integer (0, 1) | no | Optimizes streams for faster playback and decoding |
| `enable_dlf` | integer (0, 1) | no | Enables or disables the deblocking loop filter |
| `enable_restoration` | integer (1 or 0) | no | Enables restoration filtering for enhanced quality |
| `hierarchical_levels` | integer (0, 1, 2, 3) | no | Defines the depth of hierarchical prediction structure |
| `pred_struct` | integer (0, 1, 2) | no | Determines the prediction structure of frames |


##### `start_encode2.query.format[].stream`  
_type: array of objects_

List of ABR streams

| Name | Type | Req | Description |
|---|---|---|---|
| `chunklist_name` | string | no | Custom chunklist name |


##### `start_encode2.query.format[].subtitles`  
_type: object_

Closed captions configuration

| Name | Type | Req | Description |
|---|---|---|---|
| `sources` | array of objects | no | List of subtitles sources |
| `copy` | integer (1 or 0) | no | Enables copying of eia608 or eia708 captions |


###### `start_encode2.query.format[].subtitles.sources`  
_type: array of objects_

List of subtitles sources

| Name | Type | Req | Description |
|---|---|---|---|
| `source` | string | yes | Subtitles URL |
| `language` | string | yes | Subtitles language |


##### `start_encode2.query.format[].logo`  
_type: object or array of objects_

Adds watermark / logo to a video output

| Name | Type | Req | Description |
|---|---|---|---|
| `source` | string | yes | Logo or watermark image url |
| `x` | integer | no | Image X position |
| `y` | integer | no | Image Y position |
| `opacity` | float (from 0 to 1) | no | Watermark opacity |
| `start_time` | float | no | Start time for dynamic logo |
| `duration` | float | no | Duration for dynamic watermark |


##### `start_encode2.query.format[].cenc_drm`  
_type: object_

Widevine and Playready DRM encryption parameters

| Name | Type | Req | Description |
|---|---|---|---|
| `key` | string (hex) | yes | DRM encryption key |
| `key_id` | string (hex) | yes | DRM encryption key id |
| `iv` | string (hex) | no | DRM encryption IV |
| `pssh` | string (base64) | yes | DRM encryption PSSH |
| `la_url` | string | no | License server URL |


##### `start_encode2.query.format[].fps_drm`  
_type: object_

Fairplay DRM encryption parameters

| Name | Type | Req | Description |
|---|---|---|---|
| `key` | string (hex) | yes | DRM encryption key |
| `iv` | string (hex) | yes | DRM encryption key IV |
| `key_url` | string | yes | Encryption key URL |


##### `start_encode2.query.format[].encryption`  
_type: object_

AES-128 encryption parameters

| Name | Type | Req | Description |
|---|---|---|---|
| `key` | string (hex) | yes | Encryption key |
| `iv` | string (hex) | yes | Encryption key IV |
| `key_url` | string | yes | Encryption key URL |


##### `start_encode2.query.format[].inject_360_metadata`  
_type: object_

Specifies metadata attributes for 360° or VR180 video formats, including projection type, stereoscopic mode, and optional VR180 crop geometry.

| Name | Type | Req | Description |
|---|---|---|---|
| `side_data_type` | string | no | Specifies the type of auxiliary or embedded video metadata to include, such as spatial (360/VR) or stereoscopic layout information. |
| `projection` | string | no | Defines the geometric projection type of the video, indicating how the 360° or VR content is mapped onto a flat surface. |
| `vr180` | integer (0 or 1) | no | Indicates whether the video uses the VR180 format, capturing only the front 180° field of view with optional stereoscopic depth. |
| `stereo` | string | no | Specifies the stereoscopic layout of the video frames, defining how left and right eye views are arranged for 3D playback. |
| `full_width` | integer | no | Specifies the total pixel width of the full video frame before cropping. |
| `full_height` | integer | no | Specifies the total pixel height of the full video frame before cropping. |
| `cropped_width` | integer | no | Defines the width in pixels of the cropped (visible) region within the full video frame. |
| `cropped_height` | integer | no | Defines the height in pixels of the cropped (visible) region within the full video frame. |
| `cropped_left` | integer | no | Specifies the horizontal offset (in pixels) of the cropped region’s left edge from the full frame’s left boundary. |
| `cropped_top` | integer | no | Specifies the vertical offset (in pixels) of the cropped region’s top edge from the full frame’s top boundary. |


**Returns:**

| Name | Type | Req | Description |
|---|---|---|---|
| `status_url` | — | no | URL used to get the status of a transcoding job |


---

## `POST /v1/status` <a id="status"></a>

Gets the current status of one or more transcoding jobs. The https://api.qencode.com/v1/status endpoint is a quick way to get feedback on whether the job is still running or has already completed. The master endpoint https://<master>/v1/status let's you get a more complete set of information about a job. This endpoint url is returned in the status_url attribute of the job's status object.

**Arguments:**

| Name | Type | Req | Description |
|---|---|---|---|
| `task_tokens` | list | yes | A list of task tokens to get the status for. |


**Returns:**

| Name | Type | Req | Description |
|---|---|---|---|
| `statuses` | — | no | Task statuses |


**`status` object** (referenced by returns above):

### `status.returns.status`  
_type: object_

Task status

| Name | Type | Req | Description |
|---|---|---|---|
| `status` | string | no | Current task status |
| `status_url` | string | no | Status endpoint |
| `percent` | float | no | Completion percent |
| `error` | integer (0 or 1) | no | Error state |
| `error_description` | string | no | Error message |
| `warnings` | array of objects | no | List of warnings for the job |
| `videos` | array of objects | no | List of video statuses |
| `audios` | array of objects | no | List of audio statuses |
| `images` | array of objects | no | List of image statuses |
| `texts` | array of objects | no | List of text statuses |


#### `status.returns.status.warnings`  
_type: array of objects_

List of warnings for the job

| Name | Type | Req | Description |
|---|---|---|---|
| `message` | string | no | Warning message |
| `details` | string | no | Warning details |
| `tag` | string | no | Output system tag |


#### `status.returns.status.videos`  
_type: array of objects_

List of video statuses

| Name | Type | Req | Description |
|---|---|---|---|
| `status` | string | no | Current subtask status |
| `percent` | string | no | Percent of encoding completion |
| `url` | string | no | Image URL |
| `tag` | string | no | System tag |
| `user_tag` | string | no | User tag |
| `bitrate` | integer | no | Video bitrate in kbps |
| `duration` | float | no | Video duration in seconds |
| `meta` | string | no | Additional video information |
| `size` | float | no | Video size in megabytes |
| `error` | string | no | Error status |
| `error_description` | string | no | Error message |


#### `status.returns.status.audios`  
_type: array of objects_

List of audio statuses

| Name | Type | Req | Description |
|---|---|---|---|
| `url` | string | no | Image URL |
| `tag` | string | no | System tag |
| `user_tag` | string | no | User tag |


#### `status.returns.status.images`  
_type: array of objects_

List of image statuses

| Name | Type | Req | Description |
|---|---|---|---|
| `url` | string | no | Image URL |
| `tag` | string | no | System tag |
| `user_tag` | string | no | User tag |


#### `status.returns.status.texts`  
_type: array of objects_

List of text statuses

| Name | Type | Req | Description |
|---|---|---|---|
| `url` | string | no | Image URL |
| `tag` | string | no | System tag |
| `user_tag` | string | no | User tag |
| `detected_language` | string | no | Detected language |


---

## `OPTIONS, POST, PATCH /v1/upload_file` <a id="upload_file"></a>

Provides endpoint for direct video file upload using the TUS protocol for resumable uploads. Endpoint URL is returned with /v1/create_task method. You must add task_token value to the URL when performing upload, so the full URL is: https://<storage_host>/v1/upload_file/<task_token> You probably should not implement TUS protocol from scratch. We have tus uploads integrated in most of our SDKs , see examples in the right column. You can also use different client implementations from tus.io .

**Arguments:**

| Name | Type | Req | Description |
|---|---|---|---|
| `task_token` | string | yes | Task token |


**Returns:**

| Name | Type | Req | Description |
|---|---|---|---|
| `file_uuid` | — | no | TUS file uuid |


---
