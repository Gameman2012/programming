obs = obslua

function on_event(event)
    if event == obs.OBS_FRONTEND_EVENT_RECORDING_STOPPED then
        -- جلب مسار آخر فيديو تم تسجيله
        local last_recording = obs.obs_frontend_get_last_recording()
        if last_recording and last_recording ~= "" then
            -- فتح الفيديو باستخدام المشغل الافتراضي للنظام
            os.execute('xdg-open "' .. last_recording .. '" &')
        end
    end
end

function script_load(settings)
    obs.obs_frontend_add_event_callback(on_event)
end
