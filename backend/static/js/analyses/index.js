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


// =====================================================
// 4. 이벤트 연결 (사용자가 뭔가 하면 → 어떤 함수를 실행할지)
// =====================================================
selectBtn.addEventListener("click", () => {
  console.log("[파일선택] 버튼 클릭됨");   // 확인용 로그
  fileInput.click();
});

fileInput.addEventListener("change", () => {
  const file = fileInput.files[0];   // 고른 파일들 중 첫 번째

  // 파일창을 열었다가 [취소]를 누르면 file이 없음 → 아무것도 안 하고 끝
  if (!file) {
    console.log("파일 선택 취소됨");
    return;
  }

  // 확인용: 파일 정보 출력
  console.log("이름:", file.name);
  console.log("종류:", file.type);
  console.log("크기:", (file.size / (1024 * 1024)).toFixed(1) + " MB");

  const error = validateVideo(file);
  if (error) {
    statusText.textContent = error;   // 화면의 결과 영역에 에러 표시
    console.warn("검사 실패:", error);
    fileInput.value = "";             // 초기화 → 같은 파일을 다시 골라도 change가 일어나게
    return;
  }

  statusText.textContent = `선택됨: ${file.name}`;
  console.log("검사 통과");

});

