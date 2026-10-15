<script lang="ts">
  import { onDestroy } from 'svelte';

  type Locale = 'en' | 'zh-TW' | 'zh-CN';
  type Mode = 'download' | 'convert' | 'assistant';
  type Job = { name: string; detail: string; status: 'ready' | 'running' | 'complete'; progress: number };

  const copy = {
    en: {
      navProject: 'Project', navWorkflows: 'Workflows', navAbout: 'About', tryDemo: 'Try the demo', tryFlow: 'Try this flow',
      title: 'A field guide to\nMultimedia Downloader.', intro: 'An open-source, cross-platform project for downloading and converting media. Explore its everyday workflows without installing anything.',
      demoLabel: 'Interactive app preview', simulated: 'SIMULATION · LOCAL ONLY', fieldGuide: 'FIELD GUIDE', mediaTools: 'MEDIA TOOLS', openSource: 'Open source', inBrowser: 'IN THE BROWSER', localSimulation: 'LOCAL SIMULATION',
      tabDownload: 'Download', tabConvert: 'Convert', tabAssistant: 'AI assistant', urlLabel: 'Media URL', urlPlaceholder: 'Paste a video or audio link', formatLabel: 'Output format', startDownload: 'Run sample download', startConvert: 'Run sample conversion', askAssistant: 'Draft a plan',
      queueTitle: 'Activity', queueEmpty: 'Your next example will appear here.', sampleTitle: 'Example item', sampleDetail: 'Sample media · 1080p', ready: 'Ready to preview', running: 'Simulating task…', complete: 'Example complete', output: 'Example output',
      expand: 'Open full view', close: 'Close full view', demoNotice: 'This is a browser-only simulation. It does not contact media sites, download files, or convert media.',
      workflowTitle: 'Three workflows, one queue.', workflowIntro: 'Explore the shape of the real app: provide an input, choose an output, and review the result. Here, every value is fictional.',
      downloadTitle: 'Bring a media link', downloadBody: 'The real app uses yt-dlp to retrieve supported video and audio sources, with options for quality, subtitles, and cookies where needed.',
      convertTitle: 'Change the format', convertBody: 'Choose a source file and an output format. The real app uses ffmpeg for audio extraction and media conversion.',
      assistantTitle: 'Review before running', assistantBody: 'Describe a batch task and the assistant drafts a queue. In the real app, nothing runs until you confirm the plan.',
      assistantPlaceholder: 'e.g. Convert these clips to MP4', planReady: 'Draft plan', confirm: 'Confirm sample plan', cancel: 'Clear plan', confirmation: 'Plan confirmed. A fictional example was added to Activity.',
      sourceFile: 'Example source file', selectExample: 'Select a sample file', formatMp4: 'MP4 video', formatMp3: 'MP3 audio', formatWav: 'WAV audio', formatFlac: 'FLAC audio', formatWebm: 'WebM video',
      aboutTitle: 'A cross-platform downloader and converter.', aboutBody: 'Multimedia Downloader combines yt-dlp and ffmpeg in an open-source app for Windows, macOS, Linux, and web. The project also includes an optional AI assistant for planning batch work.',
      facts: ['Video and audio downloads', 'Format conversion and audio extraction', 'Batch queue with per-item progress', 'English, 繁體中文, 简体中文'],
      stepsTitle: 'A simple path through the app.', steps: [{ title: 'Add an input', body: 'Paste a supported media URL or choose a local file.' }, { title: 'Set the output', body: 'Pick a format and the options relevant to your task.' }, { title: 'Review the queue', body: 'Check the example items and progress before they finish.' }],
      sourceTitle: 'Explore the actual project.', sourceBody: 'This site is a guided preview. Visit the repository for source code, releases, and the full user manual. Join the Discord community to meet other users.', sourceCta: 'View the GitHub repository', communityCta: 'Join the Discord community', language: 'Language', footer: 'A learning preview for Multimedia Downloader.', source: 'Project source', community: 'Discord community',
      urlType: 'URL', videoSource: 'VIDEO SOURCE', resolution: '1080p · MP4', recording: 'FIELD RECORDING', stereo: '48 kHz · Stereo', proposedQueue: 'PROPOSED QUEUE', reviewRequired: 'REVIEW REQUIRED', sampleClipA: 'Sample clip A', sampleClipB: 'Sample clip B', nothingRuns: 'Nothing runs until confirmed.', confirmPlan: 'Confirm plan',
      mockTag: 'Fictional sample', inputRequired: 'Enter a sample URL to continue.', invalidPrompt: 'Add a short task description first.', dropped: 'Drop a sample item here',
    },
    'zh-TW': {
      navProject: '專案', navWorkflows: '工作流程', navAbout: '關於', tryDemo: '試用模擬 App', tryFlow: '試走此流程',
      title: 'Multimedia Downloader\n互動專案指南。', intro: '跨平台開源媒體下載與轉檔工具。免安裝探索專案功能並體驗常見工作流程。',
      demoLabel: '互動式 App 預覽', simulated: '模擬操作 · 僅限本機', fieldGuide: '互動指南', mediaTools: '媒體工具', openSource: '開源專案', inBrowser: '瀏覽器示範', localSimulation: '本機模擬',
      tabDownload: '下載', tabConvert: '轉檔', tabAssistant: 'AI 助理', urlLabel: '媒體網址', urlPlaceholder: '貼上影片或音訊連結', formatLabel: '輸出格式', startDownload: '執行模擬下載', startConvert: '執行模擬轉檔', askAssistant: '產生計畫草稿',
      queueTitle: '活動記錄', queueEmpty: '下一個範例會顯示在這裡。', sampleTitle: '範例項目', sampleDetail: '示範媒體 · 1080p', ready: '等待預覽', running: '正在模擬…', complete: '範例已完成', output: '範例輸出',
      expand: '展開完整介面', close: '關閉完整介面', demoNotice: '這是純瀏覽器模擬，不會連線至媒體網站、下載檔案或轉換媒體。',
      workflowTitle: '三種流程，共用一個佇列。', workflowIntro: '探索真實 App 的基本操作：提供輸入、選擇輸出、檢視結果。此處的數值與檔案皆為虛構範例。',
      downloadTitle: '加入媒體連結', downloadBody: '真實 App 透過 yt-dlp 擷取支援的影片和音訊來源，並可設定畫質、字幕與必要的 Cookie。',
      convertTitle: '轉換媒體格式', convertBody: '選擇來源檔案和輸出格式。真實 App 使用 ffmpeg 擷取音訊並轉換媒體格式。',
      assistantTitle: '確認後才執行', assistantBody: '描述批次工作，AI 助理會先產生佇列草稿。真實 App 也必須在你確認計畫後才會執行。',
      assistantPlaceholder: '例如：將這些影片轉成 MP4', planReady: '計畫草稿', confirm: '確認模擬計畫', cancel: '清除計畫', confirmation: '計畫已確認，虛構範例已加入活動記錄。',
      sourceFile: '範例來源檔案', selectExample: '選擇示範檔案', formatMp4: 'MP4 影片', formatMp3: 'MP3 音訊', formatWav: 'WAV 音訊', formatFlac: 'FLAC 音訊', formatWebm: 'WebM 影片',
      aboutTitle: '跨平台下載與轉檔工具。', aboutBody: 'Multimedia Downloader 將 yt-dlp 與 ffmpeg 整合於開源 App，支援 Windows、macOS、Linux 與 Web。專案亦包含可選用的 AI 助理，協助規劃批次工作。',
      facts: ['影片及音訊下載', '格式轉換與音訊擷取', '逐項顯示進度的批次佇列', 'English、繁體中文、简体中文'],
      stepsTitle: '輕鬆走過 App 工作流程。', steps: [{ title: '加入輸入項目', body: '貼上支援的媒體網址，或選擇本機檔案。' }, { title: '設定輸出', body: '選擇格式及符合任務需求的選項。' }, { title: '檢視佇列', body: '完成前確認範例項目與處理進度。' }],
      sourceTitle: '前往了解實際專案。', sourceBody: '此網站是導覽預覽。前往 Repository 查看原始碼、版本發佈與完整使用手冊，也歡迎加入 Discord 社群交流。', sourceCta: '查看 GitHub Repository', communityCta: '加入 Discord 社群', language: '語言', footer: 'Multimedia Downloader 學習預覽。', source: '專案原始碼', community: 'Discord 社群',
      urlType: '網址', videoSource: '影片來源', resolution: '1080p · MP4', recording: '示範錄音', stereo: '48 kHz · 立體聲', proposedQueue: '計畫佇列', reviewRequired: '需要確認', sampleClipA: '範例片段 A', sampleClipB: '範例片段 B', nothingRuns: '確認計畫前不會執行。', confirmPlan: '確認計畫',
      mockTag: '虛構範例', inputRequired: '請先輸入示範網址。', invalidPrompt: '請先簡短描述任務。', dropped: '拖曳範例項目至此',
    },
    'zh-CN': {
      navProject: '项目', navWorkflows: '工作流程', navAbout: '关于', tryDemo: '试用模拟 App', tryFlow: '体验此流程',
      title: 'Multimedia Downloader\n互动项目指南。', intro: '跨平台开源媒体下载与转换工具。免安装探索项目功能并体验常见工作流程。',
      demoLabel: '互动式 App 预览', simulated: '模拟操作 · 仅限本地', fieldGuide: '互动指南', mediaTools: '媒体工具', openSource: '开源项目', inBrowser: '浏览器演示', localSimulation: '本地模拟',
      tabDownload: '下载', tabConvert: '转换', tabAssistant: 'AI 助手', urlLabel: '媒体网址', urlPlaceholder: '粘贴视频或音频链接', formatLabel: '输出格式', startDownload: '运行模拟下载', startConvert: '运行模拟转换', askAssistant: '生成计划草稿',
      queueTitle: '活动记录', queueEmpty: '下一个示例会显示在这里。', sampleTitle: '示例项目', sampleDetail: '演示媒体 · 1080p', ready: '等待预览', running: '正在模拟…', complete: '示例已完成', output: '示例输出',
      expand: '展开完整界面', close: '关闭完整界面', demoNotice: '这是纯浏览器模拟，不会连接媒体网站、下载文件或转换媒体。',
      workflowTitle: '三种流程，共用一个队列。', workflowIntro: '探索真实 App 的基本操作：提供输入、选择输出、查看结果。此处的数值和文件都是虚构示例。',
      downloadTitle: '添加媒体链接', downloadBody: '真实 App 通过 yt-dlp 获取受支持的视频和音频来源，并可设置画质、字幕和必要的 Cookie。',
      convertTitle: '转换媒体格式', convertBody: '选择源文件和输出格式。真实 App 使用 ffmpeg 提取音频并转换媒体格式。',
      assistantTitle: '确认后才运行', assistantBody: '描述批量任务，AI 助手会先生成队列草稿。真实 App 也必须在你确认计划后才会运行。',
      assistantPlaceholder: '例如：将这些视频转换为 MP4', planReady: '计划草稿', confirm: '确认模拟计划', cancel: '清除计划', confirmation: '计划已确认，虚构示例已添加到活动记录。',
      sourceFile: '示例源文件', selectExample: '选择演示文件', formatMp4: 'MP4 视频', formatMp3: 'MP3 音频', formatWav: 'WAV 音频', formatFlac: 'FLAC 音频', formatWebm: 'WebM 视频',
      aboutTitle: '跨平台下载与转换工具。', aboutBody: 'Multimedia Downloader 将 yt-dlp 与 ffmpeg 整合到开源 App 中，支持 Windows、macOS、Linux 和 Web。项目还包含可选的 AI 助手，用于规划批量任务。',
      facts: ['视频和音频下载', '格式转换与音频提取', '逐项显示进度的批量队列', 'English、繁體中文、简体中文'],
      stepsTitle: '轻松体验 App 工作流程。', steps: [{ title: '添加输入项', body: '粘贴受支持的媒体网址，或选择本地文件。' }, { title: '设置输出', body: '选择格式和符合任务需求的选项。' }, { title: '查看队列', body: '完成前确认示例项目和处理进度。' }],
      sourceTitle: '前往了解实际项目。', sourceBody: '此网站是导览预览。前往 Repository 查看源代码、版本发布和完整用户手册，也欢迎加入 Discord 社区交流。', sourceCta: '查看 GitHub Repository', communityCta: '加入 Discord 社区', language: '语言', footer: 'Multimedia Downloader 学习预览。', source: '项目源代码', community: 'Discord 社区',
      urlType: '网址', videoSource: '视频来源', resolution: '1080p · MP4', recording: '演示录音', stereo: '48 kHz · 立体声', proposedQueue: '计划队列', reviewRequired: '需要确认', sampleClipA: '示例片段 A', sampleClipB: '示例片段 B', nothingRuns: '确认计划前不会运行。', confirmPlan: '确认计划',
      mockTag: '虚构示例', inputRequired: '请先输入演示网址。', invalidPrompt: '请先简短描述任务。', dropped: '拖动示例项目至此',
    },
  } as const;

  let locale = $state<Locale>('en');
  let mode = $state<Mode>('download');
  let url = $state('https://video.example/watch/sample');
  let format = $state('mp4');
  let sourceFile = $state('field-recording.wav');
  let prompt = $state('');
  let plan = $state(false);
  let notice = $state('');
  let expanded = $state(false);
  let progress = $state(0);
  let jobs = $state<Job[]>([]);
  let timer: ReturnType<typeof setInterval> | undefined;
  const t = $derived(copy[locale]);
  const isRunning = $derived(jobs.some((job) => job.status === 'running'));

  function outputName(input: string, nextFormat: string) {
    const safeName = input.split('/').pop()?.split('?')[0]?.replace(/\.[^.]+$/, '') || 'sample-media';
    return `${safeName}.${nextFormat}`;
  }

  function runExample(input: string, detail: string, nextFormat: string) {
    if (timer) clearInterval(timer);
    const name = outputName(input, nextFormat);
    jobs = [{ name, detail, status: 'running', progress: 0 }, ...jobs.filter((job) => job.status !== 'running')].slice(0, 4);
    progress = 0;
    timer = setInterval(() => {
      progress = Math.min(progress + 8, 100);
      jobs = jobs.map((job, index) => index === 0 ? { ...job, progress, status: progress === 100 ? 'complete' : 'running' } : job);
      if (progress === 100 && timer) {
        clearInterval(timer);
        timer = undefined;
      }
    }, 180);
  }

  function startDownload() {
    if (!url.trim()) {
      notice = t.inputRequired;
      return;
    }
    notice = '';
    runExample(url, t.sampleDetail, format);
  }

  function startConvert() {
    notice = '';
    runExample(sourceFile, t.sourceFile, format);
  }

  function draftPlan() {
    if (!prompt.trim()) {
      notice = t.invalidPrompt;
      plan = false;
      return;
    }
    notice = '';
    plan = true;
  }

  function confirmPlan() {
    plan = false;
    notice = t.confirmation;
    runExample('sample-clips', t.planReady, 'mp4');
  }

  $effect(() => {
    document.documentElement.lang = locale === 'zh-TW' ? 'zh-Hant' : locale === 'zh-CN' ? 'zh-Hans' : 'en';
  });
  onDestroy(() => { if (timer) clearInterval(timer); });
</script>

<svelte:head>
  <title>{locale === 'en' ? 'Multimedia Downloader — project field guide' : 'Multimedia Downloader — 互動專案指南'}</title>
</svelte:head>

<header class="topbar">
  <a class="wordmark" href="#top" aria-label="Multimedia Downloader home"><span class="mark" aria-hidden="true"><i></i><i></i><i></i></span><span>Multimedia<br />Downloader</span></a>
  <nav aria-label="Main navigation">
    <a href="#project">{t.navProject}</a><a href="#workflows">{t.navWorkflows}</a><a href="#about">{t.navAbout}</a>
  </nav>
  <div class="top-actions">
    <label class="language-picker"><span class="sr-only">{t.language}</span><select bind:value={locale} aria-label={t.language}><option value="en">EN</option><option value="zh-TW">繁體</option><option value="zh-CN">简体</option></select></label>
    <a class="top-cta" href="#demo">{t.tryDemo}<svg class="arrow-icon" aria-hidden="true" viewBox="0 0 16 16"><path d="M3 13 13 3M5 3h8v8" /></svg></a>
  </div>
</header>

<main id="top">
  <section class="hero page-grid" id="project">
    <div class="hero-copy">
      <h1>{t.title}</h1>
      <p class="hero-intro">{t.intro}</p>
      <div class="hero-links"><a class="text-link" href="#workflows">{t.navWorkflows}<svg class="arrow-icon down-icon" aria-hidden="true" viewBox="0 0 16 16"><path d="M8 2v11M4 9l4 4 4-4" /></svg></a><span class="open-source"><span class="status-dot"></span> {t.openSource} · V4.3.11</span></div>
    </div>
    <div class="hero-index" aria-label="Project index"><span>{t.fieldGuide}</span><b>MD / 043</b><span>{t.mediaTools}</span></div>
  </section>

  <section class="demo-section" id="demo" aria-labelledby="demo-heading">
    <div class="section-heading page-grid">
      <h2 id="demo-heading">{t.demoLabel}</h2>
      <span class="simulation-flag"><span class="status-dot"></span>{t.simulated}</span>
    </div>
    <div class:demo-expanded={expanded} class="demo-workspace" data-ui>
      <div class="app-topline">
        <div class="app-title"><span class="app-mark" aria-hidden="true"><i></i><i></i><i></i></span><strong>Multimedia Downloader</strong><span class="app-version">v4.3</span></div>
        <div class="app-window-actions"><span class="window-led"></span><button class="plain-button" aria-expanded={expanded} onclick={() => expanded = !expanded}>{expanded ? t.close : t.expand}</button></div>
      </div>
      <div class="app-body">
        <div class="workbench">
          <div class="mode-tabs" role="tablist" aria-label="Workflow">
            <button class:active={mode === 'download'} role="tab" aria-selected={mode === 'download'} onclick={() => { mode = 'download'; notice = ''; }}>{t.tabDownload}</button>
            <button class:active={mode === 'convert'} role="tab" aria-selected={mode === 'convert'} onclick={() => { mode = 'convert'; notice = ''; }}>{t.tabConvert}</button>
            <button class:active={mode === 'assistant'} role="tab" aria-selected={mode === 'assistant'} onclick={() => { mode = 'assistant'; notice = ''; }}>{t.tabAssistant}</button>
          </div>
          {#if mode === 'download'}
            <div class="form-panel" role="tabpanel">
              <label class="field-label" for="media-url">{t.urlLabel}</label>
              <div class="input-with-index"><span class="input-index">{t.urlType}</span><input id="media-url" type="url" bind:value={url} placeholder={t.urlPlaceholder} /></div>
              <label class="field-label" for="download-format">{t.formatLabel}</label>
              <div class="form-row"><select id="download-format" bind:value={format}><option value="mp4">{t.formatMp4}</option><option value="webm">{t.formatWebm}</option><option value="mp3">{t.formatMp3}</option><option value="wav">{t.formatWav}</option></select><button class="primary-button" onclick={startDownload} disabled={isRunning}>{t.startDownload}<svg class="arrow-icon" aria-hidden="true" viewBox="0 0 16 16"><path d="M2 8h11M9 3l5 5-5 5" /></svg></button></div>
            </div>
          {:else if mode === 'convert'}
            <div class="form-panel" role="tabpanel">
              <span class="field-label">{t.sourceFile}</span>
              <div class="file-select"><span class="file-icon" aria-hidden="true">WAV</span><select aria-label={t.selectExample} bind:value={sourceFile}><option value="field-recording.wav">field-recording.wav</option><option value="night-train.mkv">night-train.mkv</option><option value="studio-session.mov">studio-session.mov</option></select><span class="mock-chip">{t.mockTag}</span></div>
              <label class="field-label" for="convert-format">{t.formatLabel}</label>
              <div class="form-row"><select id="convert-format" bind:value={format}><option value="mp4">{t.formatMp4}</option><option value="mp3">{t.formatMp3}</option><option value="wav">{t.formatWav}</option><option value="flac">{t.formatFlac}</option><option value="webm">{t.formatWebm}</option></select><button class="primary-button" onclick={startConvert} disabled={isRunning}>{t.startConvert}<svg class="arrow-icon" aria-hidden="true" viewBox="0 0 16 16"><path d="M2 8h11M9 3l5 5-5 5" /></svg></button></div>
            </div>
          {:else}
            <div class="form-panel assistant-panel" role="tabpanel">
              <label class="field-label" for="assistant-prompt">{t.tabAssistant}</label>
              <textarea id="assistant-prompt" bind:value={prompt} placeholder={t.assistantPlaceholder} rows="2"></textarea>
              {#if plan}
                <div class="plan-review"><span class="plan-check" aria-hidden="true"><svg viewBox="0 0 16 16"><path d="m3 8 3.2 3.2L13 4.5" /></svg></span><div><strong>{t.planReady}</strong><p>{prompt}</p></div><button class="confirm-button" onclick={confirmPlan}>{t.confirm}</button></div>
              {:else}
                <button class="primary-button" onclick={draftPlan}>{t.askAssistant}<svg class="arrow-icon" aria-hidden="true" viewBox="0 0 16 16"><path d="M2 8h11M9 3l5 5-5 5" /></svg></button>
              {/if}
            </div>
          {/if}
          {#if notice}<p class="notice" role="status">{notice}</p>{/if}
          <p class="demo-disclaimer">{t.demoNotice}</p>
        </div>
        <aside class="activity-panel" aria-label={t.queueTitle}>
          <div class="activity-heading"><h3>{t.queueTitle}</h3><span class="activity-count">{jobs.length}</span></div>
          {#if jobs.length === 0}
            <div class="empty-activity"><span class="empty-mark" aria-hidden="true">+</span><p>{t.queueEmpty}</p></div>
            <div class="activity-row sample-row"><span class="media-symbol" aria-hidden="true"><svg viewBox="0 0 16 16"><path d="m5 3 8 5-8 5z" /></svg></span><div class="job-info"><strong>{t.sampleTitle}</strong><span>{t.sampleDetail}</span></div><span class="job-state">{t.ready}</span></div>
          {:else}
            {#each jobs as job, i}
              <div class="activity-row" class:current={i === 0}>
                <span class="media-symbol" aria-hidden="true">{#if job.status === 'complete'}<svg viewBox="0 0 16 16"><path d="m3 8 3.2 3.2L13 4.5" /></svg>{:else}<svg viewBox="0 0 16 16"><path d="m5 3 8 5-8 5z" /></svg>{/if}</span><div class="job-info"><strong>{job.name}</strong><span>{job.detail}</span>{#if job.status === 'running'}<span class="progress-track"><i style={`width:${job.progress}%`}></i></span>{/if}</div><span class="job-state">{job.status === 'running' ? `${job.progress}%` : job.status === 'complete' ? t.complete : t.ready}</span>
              </div>
            {/each}
          {/if}
          <div class="activity-footer"><span class="storage-led"></span><span>{t.output}: <b>browser preview</b></span></div>
        </aside>
      </div>
    </div>
    <p class="demo-caption page-grid"><span>{t.inBrowser}</span><span>{t.demoNotice}</span><span>{t.localSimulation}</span></p>
  </section>

  <section class="workflows content-section" id="workflows">
    <div class="section-lead page-grid"><h2>{t.workflowTitle}</h2><p>{t.workflowIntro}</p></div>
    <div class="workflow-list">
      <article class="workflow-row">
        <div class="workflow-copy"><h3>{t.downloadTitle}</h3><p>{t.downloadBody}</p><button class="workflow-action" onclick={() => { mode = 'download'; document.getElementById('demo')?.scrollIntoView({ behavior: 'smooth' }); }}>{t.tryFlow}<svg class="arrow-icon" aria-hidden="true" viewBox="0 0 16 16"><path d="M3 13 13 3M5 3h8v8" /></svg></button></div>
        <div class="workflow-fragment" data-ui><div class="fragment-head"><span>{t.urlType}</span><span class="mini-led"></span></div><div class="fragment-line"><b>video.example</b><span>/watch/sample</span></div><div class="fragment-meta"><span>{t.videoSource}</span><span>{t.resolution}</span></div></div>
      </article>
      <article class="workflow-row reverse">
        <div class="workflow-copy"><h3>{t.convertTitle}</h3><p>{t.convertBody}</p><button class="workflow-action" onclick={() => { mode = 'convert'; document.getElementById('demo')?.scrollIntoView({ behavior: 'smooth' }); }}>{t.tryFlow}<svg class="arrow-icon" aria-hidden="true" viewBox="0 0 16 16"><path d="M3 13 13 3M5 3h8v8" /></svg></button></div>
        <div class="workflow-fragment format-fragment" data-ui><div class="format-track"><span>WAV</span><i aria-hidden="true"><svg class="format-arrow" viewBox="0 0 18 16"><path d="M2 8h13M10 3l5 5-5 5" /></svg></i><strong>MP3</strong></div><div class="fragment-meta"><span>{t.recording}</span><span>{t.stereo}</span></div><div class="waveform" aria-hidden="true">{#each Array(40) as _, i}<i style={`--bar:${15 + ((i * 37 + 11) % 76)}%`}></i>{/each}</div></div>
      </article>
      <article class="workflow-row">
        <div class="workflow-copy"><h3>{t.assistantTitle}</h3><p>{t.assistantBody}</p><button class="workflow-action" onclick={() => { mode = 'assistant'; document.getElementById('demo')?.scrollIntoView({ behavior: 'smooth' }); }}>{t.tryFlow}<svg class="arrow-icon" aria-hidden="true" viewBox="0 0 16 16"><path d="M3 13 13 3M5 3h8v8" /></svg></button></div>
        <div class="workflow-fragment plan-fragment" data-ui><div class="fragment-head"><span>{t.proposedQueue}</span><span>{t.reviewRequired}</span></div><div class="plan-step"><span class="step-check" aria-hidden="true"><svg viewBox="0 0 16 16"><path d="m3 8 3.2 3.2L13 4.5" /></svg></span><span>{t.sampleClipA}</span><b>MP4</b></div><div class="plan-step"><span class="step-check" aria-hidden="true"><svg viewBox="0 0 16 16"><path d="m3 8 3.2 3.2L13 4.5" /></svg></span><span>{t.sampleClipB}</span><b>MP4</b></div><div class="fragment-actions"><span>{t.nothingRuns}</span><button disabled>{t.confirmPlan}</button></div></div>
      </article>
    </div>
  </section>

  <section class="steps-section content-section">
    <div class="section-lead page-grid"><h2>{t.stepsTitle}</h2></div>
    <ol class="steps-list">{#each t.steps as step}<li><h3>{step.title}</h3><p>{step.body}</p><svg class="arrow-icon step-arrow" aria-hidden="true" viewBox="0 0 16 16"><path d="M3 3v10h10M8 8l5 5" /></svg></li>{/each}</ol>
  </section>

  <section class="about-section content-section" id="about">
    <div class="about-copy"><h2>{t.aboutTitle}</h2><p>{t.aboutBody}</p><a class="text-link" href="https://github.com/SpaceSquare640/Multimedia_Downloader" target="_blank" rel="noreferrer">{t.sourceCta}<svg class="arrow-icon" aria-hidden="true" viewBox="0 0 16 16"><path d="M3 13 13 3M5 3h8v8" /></svg></a></div>
    <ul class="facts-list">{#each t.facts as fact}<li><span class="fact-mark" aria-hidden="true"></span>{fact}</li>{/each}</ul>
  </section>

  <section class="source-callout content-section">
    <div><h2>{t.sourceTitle}</h2><p>{t.sourceBody}</p></div>
    <div class="source-actions"><a class="top-cta" href="https://github.com/SpaceSquare640/Multimedia_Downloader" target="_blank" rel="noreferrer">{t.sourceCta}<svg class="arrow-icon" aria-hidden="true" viewBox="0 0 16 16"><path d="M3 13 13 3M5 3h8v8" /></svg></a><a class="community-link" href="https://discord.gg/aaUQVJeCgC" target="_blank" rel="noreferrer">{t.communityCta}<svg class="arrow-icon" aria-hidden="true" viewBox="0 0 16 16"><path d="M3 13 13 3M5 3h8v8" /></svg></a></div>
  </section>

  <footer class="site-footer"><a class="footer-name" href="#top">Multimedia Downloader<span> / {t.fieldGuide}</span></a><span>{t.footer}</span><div class="footer-links"><a href="https://github.com/SpaceSquare640/Multimedia_Downloader" target="_blank" rel="noreferrer">{t.source}<svg class="arrow-icon" aria-hidden="true" viewBox="0 0 16 16"><path d="M3 13 13 3M5 3h8v8" /></svg></a><a href="https://discord.gg/aaUQVJeCgC" target="_blank" rel="noreferrer">{t.community}<svg class="arrow-icon" aria-hidden="true" viewBox="0 0 16 16"><path d="M3 13 13 3M5 3h8v8" /></svg></a></div></footer>
</main>
