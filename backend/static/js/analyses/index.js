// =====================================================
// 1. HTML 요소 가져오기 (JS가 만질 화면 부품들)
// =====================================================
const fileInput    = document.getElementById("fileInput");     // 숨겨진 파일 선택창
const selectBtn    = document.getElementById("selectBtn");     // [파일선택] 버튼
const analyzeBtn   = document.getElementById("analyzeBtn");    // [동영상 AI 분석] 버튼
const videoPreview = document.getElementById("videoPreview");  // 동영상 미리보기 칸
const placeholder  = document.getElementById("placeholder");   // "동영상을 여기로 끌어오세요" 문구
const statusText   = document.getElementById("statusText");    // 상태·에러 메시지 자리

// 확인용: 하나라도 null이면 HTML의 id와 철자가 다른 것
console.table({ fileInput, selectBtn, analyzeBtn, videoPreview, placeholder, statusText });


// =====================================================
// 2. 설정값 · 상태 변수
// =====================================================
const MAX_SIZE_MB = 100; 

let selectedFile = null;   // 지금 선택된 파일 (기능 3에서 [분석] 버튼을 누르면 이걸 업로드)
let previewUrl = null;     // 미리보기용 임시 주소 (나중에 해제하려고 기억해 둠)

// =====================================================
// 3. 기능 함수
// =====================================================
// 파일 검사: 문제가 있으면 에러 메시지(문자열), 없으면 null
function validateVideo(file) {
  // ① 동영상이 맞는지
  if (!file.type.startsWith("video/")) {
    return `동영상 파일만 올릴 수 있어요. (선택한 파일: ${file.name})`;
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
  placeholder.hidden = false;          // "동영상을 여기로 끌어오세요" 다시 보이기

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

