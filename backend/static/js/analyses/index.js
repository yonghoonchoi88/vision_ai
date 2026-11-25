// =====================================================
// 1. HTML 요소 가져오기 (JS가 만질 화면 부품들)
// =====================================================
const fileInput    = document.getElementById("fileInput");     // 숨겨진 파일 선택창
const selectBtn    = document.getElementById("selectBtn");     // [파일선택] 버튼
const analyzeBtn   = document.getElementById("analyzeBtn");    // [동영상 AI 분석] 버튼
const videoPreview = document.getElementById("videoPreview");  // 동영상 미리보기 칸
const placeholder  = document.getElementById("placeholder");   // 안내 문구
const statusText   = document.getElementById("statusText");    // 상태·에러 메시지 자리
const resultText   = document.getElementById("resultText");    // 예측 동작 (확신도) 자리  ← ★ 추가

// 확인용: 하나라도 null이면 HTML의 id와 철자가 다른 것
console.table({ fileInput, selectBtn, analyzeBtn, videoPreview, placeholder, statusText, resultText });


// =====================================================
// 2. 설정값 · 상태 변수
// =====================================================
const MAX_SIZE_MB = 100;   // 업로드 최대 크기
const ALLOWED_EXTS = [".mp4"];   // ai_service/main.py 의 ALLOWED_EXTS 와 항상 같게 유지

// API 주소 (docs/API.md 기준, Django 끝에는 / 를 붙인다)
const API = {
  upload: "/api/videos/",      // ① 영상 업로드
  analyze: "/api/analyses/",   // ② 분석 요청 (STEP 3에서 사용)
};

let selectedFile = null;   // 지금 선택된 파일 (기능 3에서 [분석] 버튼을 누르면 이걸 업로드)
let previewUrl = null;     // 미리보기용 임시 주소 (나중에 해제하려고 기억해 둠)

// =====================================================
// 3. 기능 함수
// =====================================================
// 파일 이름에서 확장자 꺼내기: "Walk_01.MP4" → ".mp4"
function getExtension(fileName) {
  const dotIndex = fileName.lastIndexOf(".");          // 마지막 점의 위치
  if (dotIndex === -1) return "";                      // 점이 없으면 확장자 없음
  return fileName.slice(dotIndex).toLowerCase();       // 점부터 끝까지 + 소문자로
}

// 파일 검사: 문제가 있으면 에러 메시지(문자열), 없으면 null
function validateVideo(file) {
  // ① mp4 동영상이 맞는지 (종류 + 확장자 둘 다 확인)
  const ext = getExtension(file.name);
  if (!file.type.startsWith("video/") || !ALLOWED_EXTS.includes(ext)) {
    return `mp4 동영상만 올릴 수 있어요. (선택한 파일: ${file.name})`;
  }

  // ② 크기가 기준 이하인지
  const sizeMB = file.size / (1024 * 1024);
  if (sizeMB > MAX_SIZE_MB) {
    return `파일이 너무 커요. (${sizeMB.toFixed(1)}MB / 최대 ${MAX_SIZE_MB}MB)`;
  }

  return null;   // 통과
}

// 미리보기를 지우고 처음 상태로 되돌리기
function resetPreview() {
  if (previewUrl) {
    URL.revokeObjectURL(previewUrl);   // 임시 주소 해제 (메모리 정리)
    previewUrl = null;
  }
  selectedFile = null;

  videoPreview.removeAttribute("src"); // 재생기에서 영상 빼기
  videoPreview.load();                 // 재생기 상태 초기화
  videoPreview.hidden = true;          // 재생기 숨기기
  placeholder.hidden = false;          // 안내 문구 다시 보이기

  analyzeBtn.disabled = true;          // 분석 버튼 끄기
}

// 검사를 통과한 파일을 미리보기로 보여 주기
function showPreview(file) {
  if (previewUrl) URL.revokeObjectURL(previewUrl);   // 이전 영상의 임시 주소 해제

  selectedFile = file;
  previewUrl = URL.createObjectURL(file);            // 내 컴퓨터 파일 → 브라우저용 임시 주소

  videoPreview.src = previewUrl;       // 재생기에 영상 넣기
  videoPreview.hidden = false;         // 재생기 보이기
  placeholder.hidden = true;           // 안내 문구 숨기기

  analyzeBtn.disabled = false;         // 분석 버튼 켜기
}

// 입구: 파일 하나를 받아서 검사 → 미리보기 또는 초기화
// (파일선택 버튼, 드래그 앤 드롭 모두 이 함수를 사용)
function handleFile(file) {
  const error = validateVideo(file);

  if (error) {
    resetPreview();
    statusText.textContent = error;
    console.warn("검사 실패:", error);
    return;
  }

  showPreview(file);
  statusText.textContent = `선택됨: ${file.name}`;
  console.log("검사 통과 → 미리보기 표시");
}

// ① 영상 업로드: 파일을 Django에 보내고 video_id 받기
async function uploadVideo(file) {
  // 택배 상자(FormData)에 파일 담기
  // "file" = Django가 request.FILES.get("file") 로 꺼내는 이름 → 한 글자도 다르면 안 됨
  const formData = new FormData();
  formData.append("file", file);

  // 보내고 답 기다리기 (Content-Type 은 브라우저가 multipart/form-data 로 자동 설정)
  const response = await fetch(API.upload, {
    method: "POST",
    body: formData,
  });

  // 응답 본문을 JSON으로 읽기 (서버가 JSON이 아닌 에러 페이지를 보내도 멈추지 않게 빈 객체로 대체)
  const data = await response.json().catch(() => ({}));

  // 200~299가 아니면 실패 → 서버가 준 detail 메시지로 에러 던지기
  if (!response.ok) {
    throw new Error(data.detail || `업로드 실패 (HTTP ${response.status})`);
  }

  return data.video_id;   // 성공: 번호표
}

// ② 분석 요청: video_id를 보내고 AI 결과 받기
async function requestAnalysis(videoId) {
  const response = await fetch(API.analyze, {
    method: "POST",
    headers: { "Content-Type": "application/json" },   // JSON으로 보낸다고 알림
    body: JSON.stringify({ video_id: videoId }),       // JS 객체 → JSON 글자
  });

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(data.detail || `분석 실패 (HTTP ${response.status})`);
  }

  return data;   // { analysis_id, video_id, action, confidence }
}

// =====================================================
// 4. 이벤트 연결 (사용자가 뭔가 하면 → 어떤 함수를 실행할지)
// =====================================================
selectBtn.addEventListener("click", () => {
  console.log("[파일선택] 버튼 클릭됨");   // 확인용 로그
  fileInput.click();
});

// 파일창에서 파일을 고르면 → handleFile에 넘기기
fileInput.addEventListener("change", () => {
  const file = fileInput.files[0];
  if (!file) return;          // 취소한 경우

  handleFile(file);

  fileInput.value = "";       // 초기화 → 같은 파일을 다시 골라도 change가 일어나게
});

// [동영상 AI 분석] 버튼을 클릭하면 → ① 업로드 → ② 분석 → 결과 표시
analyzeBtn.addEventListener("click", async () => {
  if (!selectedFile) return;

  analyzeBtn.disabled = true;
  selectBtn.disabled = true;
  resultText.textContent = "-";                       // 이전 결과 지우기
  statusText.textContent = "업로드 중...";

  try {
    // ① 업로드
    const videoId = await uploadVideo(selectedFile);
    console.log("업로드 완료, video_id:", videoId);

    // ② 분석 요청
    statusText.textContent = "AI 분석 중... (영상 길이에 따라 수십 초 걸릴 수 있어요)";
    const result = await requestAnalysis(videoId);
    console.log("분석 결과:", result);

    // 결과 표시: 0.8734 → 87
    const percent = Math.round(result.confidence * 100);
    resultText.textContent = `${result.action} (${percent}%)`;
    statusText.textContent = "분석 완료";
  } catch (error) {
    console.error("처리 실패:", error);
    statusText.textContent = `오류: ${error.message}`;
  } finally {
    analyzeBtn.disabled = false;
    selectBtn.disabled = false;
  }
});