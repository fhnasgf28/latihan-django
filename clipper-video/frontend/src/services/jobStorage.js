export const jobStorage = {
    saveJob(job) {
        console.log('🔍 [jobStorage] Saving job to localStorage:', job)
        localStorage.setItem('current_job', JSON.stringify({
            id: job.id,
            access_token: job.access_token,
            status: job.status,
            progress: job.progress,
            created_at: job.created_at
        }))
        console.log('✅ [jobStorage] Job saved successfully')
    },
    
    getJob() {
        const stored = localStorage.getItem('current_job')
        console.log('🔍 [jobStorage] Retrieved from localStorage:', stored)
        const job = stored ? JSON.parse(stored) : null
        console.log('🔍 [jobStorage] Parsed job:', job)
        return job
    },
    
    clearJob() {
        console.log('🗑️ [jobStorage] Clearing job from localStorage')
        localStorage.removeItem('current_job')
        console.log('✅ [jobStorage] Job cleared successfully')
    },

    isJobValid(job) {
        if (!job) {
            console.log('❌ [jobStorage] Job is null/undefined')
            return false
        }
        if (!job.created_at) {
            console.log('⚠️ [jobStorage] created_at missing, job considered valid for backward compatibility')
            return true
        }
        const created = new Date(job.created_at)
        if (Number.isNaN(created.getTime())) {
            console.log('⚠️ [jobStorage] created_at invalid, job considered valid for backward compatibility')
            return true
        }
        const now = new Date()
        const hoursDiff = (now - created) / (1000 * 60 * 60)
        const isValid = hoursDiff < 24
        console.log(`🔍 [jobStorage] Job validity check: created=${created}, now=${now}, hoursDiff=${hoursDiff.toFixed(2)}, valid=${isValid}`)
        return isValid
    }
}
