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
// (STEP 3, 4에서 채움)


// =====================================================
// 3. 기능 함수
// =====================================================
// (STEP 3, 4에서 채움)


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
});