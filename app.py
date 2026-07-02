import streamlit as st
import pandas as pd
import io

# ==============================================================================
# 1. CẤU HÌNH TRANG WEB CỦA ỨNG DỤNG
# ==============================================================================
st.set_page_config(page_title="Hệ Thống Tính Thuế & Chi Phí Nhân Sự 2026", page_icon="📊", layout="centered")

# --- CHÈN LOGO THEO FILE TRỰC TIẾP ---
try:
    st.image("logo.jpg")
except:
    pass # Bỏ qua nếu chưa có file logo ở thư mục chạy

# --- THÔNG TIN THÀNH VIÊN VÀ ĐỀ TÀI ---
st.markdown("### 📝 **ĐỀ TÀI 5_Trần Thị Phượng 23030066_Nguyễn Thị Như Ý 23030077_Trần Tấn Phát 23030089_Nguyễn Xuân Tài 23030262_Đỗ Nguyễn Trúc Linh 23120087_Phan Thị Lan Thanh 23030094_Nguyễn Hoàng Phúc 23030061_Nguyễn Minh Tâm 23030232 **")
st.title("📊 Hệ Thống Quản Lý Tài Chính & Thu Thập Thuế 2026")
st.write("Giải pháp tích hợp tính Thuế TNCN (Dành cho Người lao động) và Chi phí nhân sự (Dành cho Doanh nghiệp)")
st.markdown("---")

# --- KHỞI TẠO BỘ NHỚ LƯU TRỮ LỊCH SỬ (SESSION STATE) ---
if "lich_su_nld" not in st.session_state:
    st.session_state.lich_su_nld = []
if "lich_su_dn" not in st.session_state:
    st.session_state.lich_su_dn = []


# ==============================================================================
# 2. PHÂN LUỒNG NGƯỜI DÙNG (ROUTING)
# ==============================================================================
st.subheader("🚀 Vui lòng chọn vai trò của bạn để tiếp tục:")
vai_tro = st.radio(
    "Bạn là:",
    ("👤 Người lao động (Tính lương Net & Thuế TNCN)", "🏢 Người sử dụng lao động / Doanh nghiệp (Tính Total Cost & Bảo hiểm)"),
    index=0,
    horizontal=True
)

st.markdown("---")


# ==============================================================================
# 3. NHÁNH 1: DÀNH CHO NGƯỜI LAO ĐỘNG
# ==============================================================================
if "👤 Người lao động" in vai_tro:
    st.subheader("📋 Nhập thông tin thu nhập tháng này của bạn")
    
    gross_salary = st.number_input("1. Lương đóng BHXH (VND):", min_value=0, value=30000000, step=500000, format="%d", key="nld_gross")
    gross_bonus_pay = st.number_input("2. Tiền thưởng / Bonus (VND):", min_value=0, value=0, step=500000, format="%d", key="nld_bonus")
    overtime_pay = st.number_input("3. Tiền lương tăng ca / làm thêm giờ (VND):", min_value=0, value=0, step=500000, format="%d", key="nld_overtime")

    st.markdown("**4. Các khoản phụ cấp nhận bằng tiền mặt:**")
    col_sub1, col_sub2 = st.columns(2)
    with col_sub1:
        lunch_allowance = st.number_input("Phụ cấp ăn trưa (VND):", min_value=0, value=0, step=50000, key="nld_lunch")
    with col_sub2:
        other_allowance = st.number_input("Phụ cấp điện thoại, xăng xe (VND):", min_value=0, value=0, step=50000, key="nld_other")

    dependents = st.number_input("5. Số người phụ thuộc bạn đang nuôi dưỡng (người):", min_value=0, value=1, step=1, key="nld_deps")
    st.markdown("---")

    # Logic tính toán cho Người lao động
    def tinh_thue_tncn(gross, bonus, overtime, lunch, other, deps):
        total_income = gross + bonus + overtime + lunch + other
        bhxh = gross * 0.08
        bhyt = gross * 0.015
        bhtn = gross * 0.01
        total_insurance = bhxh + bhyt + bhtn
        
        self_reduction = 15500000  
        dependent_reduction = deps * 6200000  
        total_reduction = self_reduction + dependent_reduction
        
        exempt_lunch = min(lunch, 730000)
        exempt_allowance = other  
        total_exempt_income = overtime + exempt_lunch + exempt_allowance
        
        assessable_income = max(0, total_income - total_exempt_income - total_insurance - total_reduction)
        
        tax = 0
        brackets = [
            {"limit": 10000000, "rate": 0.05, "desc": "Bậc 1: Đến 10 triệu đồng (5%)"},
            {"limit": 30000000, "rate": 0.10, "desc": "Bậc 2: Trên 10 đến 30 triệu đồng (10%)"},
            {"limit": 60000000, "rate": 0.20, "desc": "Bậc 3: Trên 30 đến 60 triệu đồng (20%)"},
            {"limit": 100000000, "rate": 0.30, "desc": "Bậc 4: Trên 60 đến 100 triệu đồng (30%)"},
            {"limit": float('inf'), "rate": 0.35, "desc": "Bậc 5: Trên 100 triệu đồng (35%)"}
        ]
        
        temp_income = assessable_income
        previous_limit = 0
        tax_breakdown = []
        
        for b in brackets:
            range_size = b["limit"] - previous_limit
            if temp_income > 0:
                taxable_in_bracket = min(temp_income, range_size)
                tax_in_bracket = taxable_in_bracket * b["rate"]
                tax += tax_in_bracket
                
                tax_breakdown.append({
                    "Bậc thuế": b["desc"],
                    "Thu nhập tính thuế ở bậc này": f"{taxable_in_bracket:,.0f} VNĐ",
                    "Tiền thuế phải nộp": f"{tax_in_bracket:,.0f} VNĐ"
                })
                temp_income -= taxable_in_bracket
            previous_limit = b["limit"]
                
        net_salary = total_income - total_insurance - tax
        
        return {
            "total_income": total_income, "bhxh": bhxh, "bhyt": bhyt, "bhtn": bhtn, 
            "total_insurance": total_insurance, "dependent_reduction": dependent_reduction,
            "exempt_lunch": exempt_lunch, "exempt_allowance": exempt_allowance,
            "assessable_income": assessable_income, "tax_breakdown": tax_breakdown,
            "tax": tax, "net_salary": net_salary
        }

    if st.button("🧮 Tính Thuế & Nhận Kết Quả", type="primary"):
        res = tinh_thue_tncn(gross_salary, gross_bonus_pay, overtime_pay, lunch_allowance, other_allowance, dependents)
        
        # --- Ghi dữ liệu tính toán vào lịch sử ---
        st.session_state.lich_su_nld.append({
            "Thời gian": pd.Timestamp.now().strftime("%d/%m/%Y %H:%M:%S"),
            "Lương đóng BHXH (VND)": gross_salary,
            "Tiền thưởng/Bonus (VND)": gross_bonus_pay,
            "Lương tăng ca (VND)": overtime_pay,
            "Phụ cấp ăn trưa (VND)": lunch_allowance,
            "Phụ cấp khác (VND)": other_allowance,
            "Số người phụ thuộc": dependents,
            "Tổng thu nhập (VND)": res['total_income'],
            "Tổng BH bắt buộc (VND)": res['total_insurance'],
            "Thuế TNCN phải nộp (VND)": res['tax'],
            "Thực nhận NET (VND)": res['net_salary']
        })

        st.markdown("---")
        st.subheader("🎯 Kết Quả Tính Toán Tóm Tắt")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric(label="Tổng thu nhập nhận được (Lương + Thưởng + Phụ cấp)", value=f"{res['total_income']:,.0f} VND")
            st.metric(label="Tổng bảo hiểm bắt buộc trừ vào lương (10.5%)", value=f"{res['total_insurance']:,.0f} VND")
        with col2:
            st.metric(label="Thuế TNCN phải nộp", value=f"{res['tax']:,.0f} VND")
            st.metric(label="THỰC NHẬN VỀ TAY (NET)", value=f"{res['net_salary']:,.0f} VND")
            
        st.markdown("---")
        st.subheader("📜 Giải Trình Chi Tiết Quy Trình Khấu Trừ (Năm 2026)")
        st.markdown(f"""
        * **Tổng thu nhập phát sinh trong tháng:** `{res['total_income']:,.0f} VND`
        * **Các khoản được miễn trừ thuế:**
            * Tiền lương tăng ca: `{overtime_pay:,.0f} VND`
            * Tiền ăn trưa được miễn: `{res['exempt_lunch']:,.0f} VND`
            * Phụ cấp công việc (xăng xe, điện thoại): `{res['exempt_allowance']:,.0f} VND`
        * **Các khoản phí bảo hiểm bắt buộc trích từ lương chính:**
            * BHXH (8%): `{res['bhxh']:,.0f} VND` | BHYT (1.5%): `{res['bhyt']:,.0f} VND` | BHTN (1%): `{res['bhtn']:,.0f} VND`
            * **Tổng phí bảo hiểm:** `{res['total_insurance']:,.0f} VND`
        * **Giảm trừ gia cảnh:**
            * Giảm trừ bản thân người nộp: `15,500,000 VND`
            * Giảm trừ người phụ thuộc: `{res['dependent_reduction']:,.0f} VND` (cho {dependents} người)
        * **Thu nhập tính thuế (đưa vào bảng lũy tiến):** `{res['assessable_income']:,.0f} VND`
        """)
        
        if res['tax'] > 0:
            st.write("📊 **Chi tiết phân tách số tiền nộp theo biểu thuế lũy tiến mới:**")
            st.table(res['tax_breakdown'])
        else:
            st.success("Tuyệt vời! Sau khi trừ các khoản phụ cấp miễn thuế và giảm trừ gia cảnh, thu nhập tính thuế của bạn bằng 0 nên không cần phải nộp thuế TNCN.")

    # --- HIỂN THỊ VÀ XUẤT FILE EXCEL CHO NGƯỜI LAO ĐỘNG ---
    if st.session_state.lich_su_nld:
        st.markdown("---")
        st.subheader("🕒 Lịch Sử Các Lần Tính Toán")
        df_nld = pd.DataFrame(st.session_state.lich_su_nld)
        
        # Format hiển thị trên giao diện cho đẹp
        st.dataframe(df_nld.style.format({
            "Lương đóng BHXH (VND)": "{:,.0f}", "Tiền thưởng/Bonus (VND)": "{:,.0f}", "Lương tăng ca (VND)": "{:,.0f}",
            "Phụ cấp ăn trưa (VND)": "{:,.0f}", "Phụ cấp khác (VND)": "{:,.0f}", "Tổng thu nhập (VND)": "{:,.0f}",
            "Tổng BH bắt buộc (VND)": "{:,.0f}", "Thuế TNCN phải nộp (VND)": "{:,.0f}", "Thực nhận NET (VND)": "{:,.0f}"
        }))
        
        # Build file excel truyền vào st.download_button
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_nld.to_excel(writer, index=False, sheet_name="Lịch sử Thuế TNCN")
        excel_data = output.getvalue()
        
        st.download_button(
            label="📥 Xuất lịch sử tính toán sang file Excel",
            data=excel_data,
            file_name="lich_su_tinh_thue_NLD_2026.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="secondary"
        )


# ==============================================================================
# 4. NHÁNH 2: DÀNH CHO DOANH NGHIỆP (NSDLĐ)
# ==============================================================================
else:
    st.subheader("📋 Nhập thông tin quỹ lương tháng của nhân viên")
    
    dn_gross = st.number_input("1. Mức lương chính ký hợp đồng / Đóng BHXH (VND):", min_value=0, value=30000000, step=500000, format="%d", key="dn_gross_input")
    dn_bonus = st.number_input("2. Tiền thưởng / Bonus chi trả trong tháng (VND):", min_value=0, value=0, step=500000, format="%d", key="dn_bonus_input")
    dn_overtime = st.number_input("3. Tiền lương tăng ca / làm thêm giờ (VND):", min_value=0, value=0, step=500000, format="%d", key="dn_overtime_input")

    st.markdown("**4. Các khoản phụ cấp, phúc lợi hỗ trợ nhân viên:**")
    col_sub1, col_sub2 = st.columns(2)
    with col_sub1:
        dn_lunch = st.number_input("Phụ cấp ăn trưa (VND):", min_value=0, value=0, step=50000, key="dn_lunch_input")
    with col_sub2:
        dn_other = st.number_input("Phụ cấp khác (Điện thoại, xăng xe, nhà ở) (VND):", min_value=0, value=0, step=50000, key="dn_other_input")

    st.markdown("---")

    # Logic tính toán cho Doanh nghiệp
    def tinh_chi_phi_nsdld(gross, bonus, overtime, lunch, other):
        direct_salary_cost = gross + bonus + overtime + lunch + other
        
        nsdld_bhxh_huu_tri = gross * 0.14       
        nsdld_bhxh_om_thai = gross * 0.03       
        nsdld_bhxh_tnld = gross * 0.005         
        nsdld_bhtn = gross * 0.01               
        nsdld_bhyt = gross * 0.03               
        
        total_nsdld_insurance = nsdld_bhxh_huu_tri + nsdld_bhxh_om_thai + nsdld_bhxh_tnld + nsdld_bhtn + nsdld_bhyt
        total_corporate_cost = direct_salary_cost + total_nsdld_insurance
        
        return {
            "direct_salary_cost": direct_salary_cost,
            "bhxh_huu_tri": nsdld_bhxh_huu_tri,
            "bhxh_om_thai": nsdld_bhxh_om_thai,
            "bhxh_tnld": nsdld_bhxh_tnld,
            "bhtn": nsdld_bhtn,
            "bhyt": nsdld_bhyt,
            "total_nsdld_insurance": total_nsdld_insurance,
            "total_corporate_cost": total_corporate_cost
        }

    if st.button("🏢 Tính Toán Chi Phí Doanh Nghiệp", type="primary"):
        res_dn = tinh_chi_phi_nsdld(dn_gross, dn_bonus, dn_overtime, dn_lunch, dn_other)
        
        # --- Ghi dữ liệu tính toán vào lịch sử ---
        st.session_state.lich_su_dn.append({
            "Thời gian": pd.Timestamp.now().strftime("%d/%m/%Y %H:%M:%S"),
            "Lương đóng BHXH (VND)": dn_gross,
            "Tiền thưởng (VND)": dn_bonus,
            "Lương tăng ca (VND)": dn_overtime,
            "Phụ cấp ăn trưa (VND)": dn_lunch,
            "Phụ cấp khác (VND)": dn_other,
            "Tổng lương trực tiếp (VND)": res_dn['direct_salary_cost'],
            "BHXH Hưu trí 14% (VND)": res_dn['bhxh_huu_tri'],
            "BHXH Ốm thai 3% (VND)": res_dn['bhxh_om_thai'],
            "BH TNLD-BNN 0.5% (VND)": res_dn['bhxh_tnld'],
            "BHYT Doanh nghiệp 3% (VND)": res_dn['bhyt'],
            "BHTN Doanh nghiệp 1% (VND)": res_dn['bhtn'],
            "Tổng BH Doanh nghiệp gánh (VND)": res_dn['total_nsdld_insurance'],
            "TỔNG CHI PHÍ NHÂN SỰ (VND)": res_dn['total_corporate_cost']
        })

        st.markdown("---")
        st.subheader("🎯 Tổng Hợp Chi Phí Nhân Sự (Tổng Doanh Nghiệp Chi)")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric(label="Tổng lương + phụ cấp trả trực tiếp cho NLĐ", value=f"{res_dn['direct_salary_cost']:,.0f} VND")
            st.metric(label="Tổng tiền bảo hiểm NSDLĐ phải đóng (21.5%)", value=f"{res_dn['total_nsdld_insurance']:,.0f} VND")
        with col2:
            st.metric(label="TỔNG CHI PHÍ THỰC TẾ CỦA DOANH NGHIỆP", value=f"{res_dn['total_corporate_cost']:,.0f} VND")
            
        st.markdown("---")
        st.subheader("📜 Bảng Giải Trình Nghĩa Vụ Trích Đóng Bảo Hiểm Của Doanh Nghiệp")
        
        insurance_data = [
            {"Hạng mục trích đóng": "Bảo hiểm Xã hội (Hưu trí, Tử tuất)", "Tỷ lệ áp dụng": "14.0%", "Số tiền đóng (VND)": f"{res_dn['bhxh_huu_tri']:,.0f} VND"},
            {"Hạng mục trích đóng": "Bảo hiểm Xã hội (Ốm đau, Thai sản)", "Tỷ lệ áp dụng": "3.0%", "Số tiền đóng (VND)": f"{res_dn['bhxh_om_thai']:,.0f} VND"},
            {"Hạng mục trích đóng": "Bảo hiểm TNLĐ - BNN", "Tỷ lệ áp dụng": "0.5%", "Số tiền đóng (VND)": f"{res_dn['bhxh_tnld']:,.0f} VND"},
            {"Hạng mục trích đóng": "Bảo hiểm Y tế (BHYT)", "Tỷ lệ áp dụng": "3.0%", "Số tiền đóng (VND)": f"{res_dn['bhyt']:,.0f} VND"},
            {"Hạng mục trích đóng": "Bảo hiểm Thất nghiệp (BHTN)", "Tỷ lệ áp dụng": "1.0%", "Số tiền đóng (VND)": f"{res_dn['bhtn']:,.0f} VND"},
        ]
        
        st.table(insurance_data)
        st.info("💡 **Lưu ý kế toán:** Tổng chi phí thực tế của doanh nghiệp (Total Cost) là cơ sở để lập ngân sách nhân sự và tính toán chi phí được trừ khi xác định thuế Thu nhập Doanh nghiệp (TNDN).")

    # --- HIỂN THỊ VÀ XUẤT FILE EXCEL CHO DOANH NGHIỆP ---
    if st.session_state.lich_su_dn:
        st.markdown("---")
        st.subheader("🕒 Lịch Sử Các Lần Tính Toán")
        df_dn = pd.DataFrame(st.session_state.lich_su_dn)
        
        # Format hiển thị số tiền ngăn cách hàng nghìn trên giao diện
        st.dataframe(df_dn.style.format({
            "Lương đóng BHXH (VND)": "{:,.0f}", "Tiền thưởng (VND)": "{:,.0f}", "Lương tăng ca (VND)": "{:,.0f}",
            "Phụ cấp ăn trưa (VND)": "{:,.0f}", "Phụ cấp khác (VND)": "{:,.0f}", "Tổng lương trực tiếp (VND)": "{:,.0f}",
            "BHXH Hưu trí 14% (VND)": "{:,.0f}", "BHXH Ốm thai 3% (VND)": "{:,.0f}", "BH TNLD-BNN 0.5% (VND)": "{:,.0f}",
            "BHYT Doanh nghiệp 3% (VND)": "{:,.0f}", "BHTN Doanh nghiệp 1% (VND)": "{:,.0f}", 
            "Tổng BH Doanh nghiệp gánh (VND)": "{:,.0f}", "TỔNG CHI PHÍ NHÂN SỰ (VND)": "{:,.0f}"
        }))
        
        # Build file excel truyền vào st.download_button
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_dn.to_excel(writer, index=False, sheet_name="Lịch sử Chi Phí DN")
        excel_data = output.getvalue()
        
        st.download_button(
            label="📥 Xuất lịch sử tính toán sang file Excel",
            data=excel_data,
            file_name="lich_su_chi_phi_DN_2026.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="secondary"
        )
