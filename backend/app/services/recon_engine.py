import json
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, text, and_
from app.models.staging import (
    RevUploadBatch, RevPortalTransactionStaging, RevAgencyBankScrollStaging, RevRbiLuggageStaging
)
from app.models.recon import RevReconRun, RevReconResult, RevReconLegLinkage, RevReconOverride
from app.models.exceptions import RevException, RevExceptionNote, RevExceptionLetter
from app.models.sla import RevPenalClaim
from app.models.accounting import RevSuspenseRegister
from app.models.masters import RevSystemConfig, RevSlaRule, RevAgencyBank
from app.models.common import AuditChangeLog, SystemNotification, ChartOfAccount
from app.core.exceptions import NotFoundException, BusinessException, InvalidStateTransitionException

class ReconEngineService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_runs(self) -> List[RevReconRun]:
        res = await self.db.execute(select(RevReconRun).order_by(RevReconRun.run_id.desc()))
        return list(res.scalars().all())

    async def list_results(
        self,
        status: Optional[str] = None,
        source: Optional[str] = None,
        dept: Optional[str] = None,
        pao: Optional[str] = None,
        booking_status: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        limit: int = 50
    ) -> Tuple[List[RevReconResult], int]:
        conditions = []
        if status:
            conditions.append(RevReconResult.status == status)
        if source:
            conditions.append(RevReconResult.revenue_source == source)
        if dept:
            conditions.append(RevReconResult.dept_code == dept)
        if pao:
            conditions.append(RevReconResult.pao_code == pao)
        if booking_status:
            conditions.append(RevReconResult.booking_status == booking_status)
        if search:
            s_term = f"%{search}%"
            conditions.append(
                (RevReconResult.challan_no.ilike(s_term)) |
                (RevReconResult.cin.ilike(s_term)) |
                (RevReconResult.payer_name.ilike(s_term)) |
                (RevReconResult.rev_transaction_id.ilike(s_term))
            )

        where_clause = and_(*conditions) if conditions else True
        count_q = select(func.count(RevReconResult.recon_id)).where(where_clause)
        count_res = await self.db.execute(count_q)
        total = count_res.scalar() or 0

        query = (
            select(RevReconResult)
            .where(where_clause)
            .order_by(RevReconResult.recon_id.desc())
            .offset((page - 1) * limit)
            .limit(limit)
        )
        res = await self.db.execute(query)
        items = list(res.scalars().all())

        # Collect recon IDs and batch fetch leg dates
        recon_ids = [item.recon_id for item in items]
        links_map: Dict[int, Dict[str, Any]] = {}
        if recon_ids:
            links_q = select(RevReconLegLinkage).where(RevReconLegLinkage.recon_id.in_(recon_ids))
            links_res = await self.db.execute(links_q)
            all_links = list(links_res.scalars().all())

            portal_ids = [l.portal_item_id for l in all_links if l.portal_item_id]
            scroll_ids = [l.scroll_item_id for l in all_links if l.scroll_item_id]
            rbi_ids = [l.rbi_item_id for l in all_links if l.rbi_item_id]

            portals = {}
            if portal_ids:
                p_res = await self.db.execute(select(RevPortalTransactionStaging).where(RevPortalTransactionStaging.portal_item_id.in_(portal_ids)))
                portals = {p.portal_item_id: p for p in p_res.scalars().all()}

            scrolls = {}
            if scroll_ids:
                s_res = await self.db.execute(select(RevAgencyBankScrollStaging).where(RevAgencyBankScrollStaging.scroll_item_id.in_(scroll_ids)))
                scrolls = {s.scroll_item_id: s for s in s_res.scalars().all()}

            rbis = {}
            if rbi_ids:
                r_res = await self.db.execute(select(RevRbiLuggageStaging).where(RevRbiLuggageStaging.rbi_item_id.in_(rbi_ids)))
                rbis = {r.rbi_item_id: r for r in r_res.scalars().all()}

            for l in all_links:
                if l.recon_id not in links_map:
                    links_map[l.recon_id] = {"portal_date": None, "bank_date": None, "rbi_date": None}
                if l.portal_item_id in portals and not links_map[l.recon_id]["portal_date"]:
                    links_map[l.recon_id]["portal_date"] = portals[l.portal_item_id].payment_date
                if l.scroll_item_id in scrolls and not links_map[l.recon_id]["bank_date"]:
                    links_map[l.recon_id]["bank_date"] = scrolls[l.scroll_item_id].bank_remittance_date or scrolls[l.scroll_item_id].payment_received_date
                if l.rbi_item_id in rbis and not links_map[l.recon_id]["rbi_date"]:
                    links_map[l.recon_id]["rbi_date"] = rbis[l.rbi_item_id].rbi_credit_date

        enriched = []
        for item in items:
            dates = links_map.get(item.recon_id, {})
            p_date = dates.get("portal_date") or (item.created_at.date() if item.created_at else None)
            b_date = dates.get("bank_date") or p_date
            r_date = dates.get("rbi_date") or p_date

            d_item = {
                "recon_id": item.recon_id,
                "rev_transaction_id": item.rev_transaction_id,
                "run_id": item.run_id,
                "group_key": item.group_key,
                "match_key_type": item.match_key_type,
                "challan_no": item.challan_no,
                "cpin": item.cpin,
                "cin": item.cin,
                "revenue_source": item.revenue_source,
                "dept_code": item.dept_code,
                "pao_code": item.pao_code,
                "receipt_head": item.receipt_head,
                "payer_name": item.payer_name,
                "portal_total": item.portal_total,
                "bank_total": item.bank_total,
                "rbi_total": item.rbi_total,
                "amount_difference": item.amount_difference,
                "date_variance_days": item.date_variance_days,
                "sla_delay_days": item.sla_delay_days,
                "penal_interest_amount": item.penal_interest_amount,
                "rule_applied": item.rule_applied,
                "match_type": item.match_type,
                "status": item.status,
                "flags": item.flags or [],
                "match_reason": item.match_reason,
                "booking_status": item.booking_status,
                "is_manual_override": item.is_manual_override,
                "machine_status": item.machine_status,
                "portal_date": p_date,
                "bank_date": b_date,
                "rbi_date": r_date,
                "created_at": item.created_at,
                "updated_at": item.updated_at,
                "organization_id": item.organization_id,
                "org_branch_id": item.org_branch_id,
                "created_by": item.created_by,
                "updated_by": item.updated_by,
            }
            enriched.append(d_item)

        return enriched, total

    async def get_result_detail(self, recon_id: int) -> Dict[str, Any]:
        recon = await self.db.get(RevReconResult, recon_id)
        if not recon:
            raise NotFoundException("Recon Result", recon_id)

        # Linkages
        links_q = select(RevReconLegLinkage).where(RevReconLegLinkage.recon_id == recon_id)
        links_res = await self.db.execute(links_q)
        linkages = list(links_res.scalars().all())

        portal_details = None
        bank_details = []
        rbi_details = []

        for l in linkages:
            if l.portal_item_id and not portal_details:
                p = await self.db.get(RevPortalTransactionStaging, l.portal_item_id)
                if p:
                    portal_details = {
                        "portal_item_id": p.portal_item_id,
                        "portal_name": p.portal_name,
                        "challan_no": p.challan_no,
                        "cin": p.cin,
                        "cpin": p.cpin,
                        "payer_name": p.payer_name,
                        "amount": float(p.amount),
                        "payment_date": str(p.payment_date),
                        "payment_mode": p.payment_mode,
                        "receipt_head": p.receipt_head,
                        "dept_validated": p.dept_validated
                    }
            if l.scroll_item_id:
                b = await self.db.get(RevAgencyBankScrollStaging, l.scroll_item_id)
                if b:
                    bank_details.append({
                        "scroll_item_id": b.scroll_item_id,
                        "bank_code": b.bank_code,
                        "scroll_no": b.scroll_no,
                        "bank_reference_no": b.bank_reference_no,
                        "amount": float(b.amount),
                        "received_date": str(b.payment_received_date),
                        "remittance_date": str(b.bank_remittance_date),
                        "utr_no": b.utr_no
                    })
            if l.rbi_item_id:
                r = await self.db.get(RevRbiLuggageStaging, l.rbi_item_id)
                if r:
                    rbi_details.append({
                        "rbi_item_id": r.rbi_item_id,
                        "file_reference_no": r.file_reference_no,
                        "rbi_reference_no": r.rbi_reference_no,
                        "bank_code": r.bank_code,
                        "amount": float(r.amount),
                        "credit_date": str(r.rbi_credit_date),
                        "status": r.rbi_status
                    })

        # Overrides
        over_q = select(RevReconOverride).where(RevReconOverride.recon_id == recon_id).order_by(RevReconOverride.override_id.desc())
        over_res = await self.db.execute(over_q)
        overrides = [
            {
                "override_id": o.override_id,
                "original_machine_status": o.original_machine_status,
                "proposed_status": o.proposed_status,
                "justification": o.proposer_justification,
                "decision_status": o.decision_status,
                "checker_remarks": o.checker_remarks,
                "proposed_at": str(o.proposed_at)
            }
            for o in over_res.scalars()
        ]

        # Notes / timeline
        notes = []
        if recon.rev_transaction_id:
            notes_q = select(RevExceptionNote).join(RevException, RevException.exception_id == RevExceptionNote.exception_id).where(RevException.recon_id == recon_id)
            notes_res = await self.db.execute(notes_q)
            for n in notes_res.scalars():
                notes.append({
                    "note_id": n.note_id,
                    "action_type": n.action_type,
                    "note_text": n.note_text,
                    "created_at": str(n.created_at)
                })

        return {
            "result": recon,
            "linkages": linkages,
            "portal_details": portal_details,
            "bank_details": bank_details,
            "rbi_details": rbi_details,
            "overrides": overrides,
            "notes": notes
        }

    async def execute_matching_engine(
        self,
        user_id: int,
        business_date: Optional[date] = None,
        source_code: Optional[str] = None,
        dept_code: Optional[str] = None,
        pao_code: Optional[str] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None
    ) -> RevReconRun:
        # Load system config
        cfg_res = await self.db.execute(select(RevSystemConfig).where(RevSystemConfig.config_id == 1))
        config = cfg_res.scalar_one_or_none() or RevSystemConfig(config_id=1)

        b_date = business_date or config.demo_business_date or date(2026, 9, 15)
        amt_tolerance = float(config.amount_tolerance)
        date_tolerance = int(config.date_tolerance_days)
        penal_rate = float(config.default_penal_rate_pct)

        # 1. Fetch approved Portal transactions
        p_query = select(RevPortalTransactionStaging).join(RevUploadBatch, RevUploadBatch.batch_id == RevPortalTransactionStaging.batch_id).where(RevUploadBatch.status == 'APPROVED')
        if source_code:
            p_query = p_query.where(RevPortalTransactionStaging.revenue_source == source_code)
        if dept_code:
            p_query = p_query.where(RevPortalTransactionStaging.dept_code == dept_code)
        if pao_code:
            p_query = p_query.where(RevPortalTransactionStaging.pao_code == pao_code)
        if from_date:
            p_query = p_query.where(RevPortalTransactionStaging.payment_date >= from_date)
        if to_date:
            p_query = p_query.where(RevPortalTransactionStaging.payment_date <= to_date)
        
        p_res = await self.db.execute(p_query)
        portal_records = list(p_res.scalars().all())

        # 2. Fetch approved Bank Scroll lines
        b_query = select(RevAgencyBankScrollStaging).join(RevUploadBatch, RevUploadBatch.batch_id == RevAgencyBankScrollStaging.batch_id).where(RevUploadBatch.status == 'APPROVED')
        if source_code:
            b_query = b_query.where(RevAgencyBankScrollStaging.revenue_source == source_code)
        if dept_code:
            b_query = b_query.where(RevAgencyBankScrollStaging.dept_code == dept_code)
        if pao_code:
            b_query = b_query.where(RevAgencyBankScrollStaging.pao_code == pao_code)
        b_res = await self.db.execute(b_query)
        bank_records = list(b_res.scalars().all())

        # 3. Fetch approved RBI Luggage lines
        r_query = select(RevRbiLuggageStaging).join(RevUploadBatch, RevUploadBatch.batch_id == RevRbiLuggageStaging.batch_id).where(RevUploadBatch.status == 'APPROVED')
        r_res = await self.db.execute(r_query)
        rbi_records = list(r_res.scalars().all())

        # Reset previous current flags
        await self.db.execute(update(RevReconRun).values(is_current=False))

        # Generate Recon Run No
        run_date_str = b_date.strftime("%Y%m%d")
        seq_res = await self.db.execute(text("SELECT ifms_budget.fn_rev_next_seq('RUN_SEQ', 'RUN', :dt)"), {"dt": run_date_str})
        run_no = seq_res.scalar() or f"RUN-{run_date_str}-{datetime.now().strftime('%H%M%S')}"

        recon_run = RevReconRun(
            run_no=run_no,
            business_date=b_date,
            scope_filters={"source": source_code, "dept": dept_code, "pao": pao_code, "from": str(from_date), "to": str(to_date)},
            executed_by=user_id,
            executed_at=datetime.now(),
            is_current=True
        )
        self.db.add(recon_run)
        await self.db.flush()

        # Group records by match keys
        grouped_candidates = self._group_records(portal_records, bank_records, rbi_records)

        matched_cnt = 0
        pending_cnt = 0
        suspend_cnt = 0
        rat_cnt = 0
        mismatch_cnt = 0
        duplicate_cnt = 0
        under_inv_cnt = 0
        total_reconciled_amt = Decimal("0.00")
        total_penal_interest = Decimal("0.00")

        # Process each match group through rules RR-01 to RR-08
        recon_idx = 0
        for group_key, group in grouped_candidates.items():
            recon_idx += 1
            result_data = self._apply_reconciliation_rules(group, amt_tolerance, date_tolerance, penal_rate, b_date)
            
            p_first = group["portal"][0] if group["portal"] else None
            b_first = group["bank"][0] if group["bank"] else None
            r_first = group["rbi"][0] if group["rbi"] else None

            # Determine automated date on which receipt was created / paid
            rec_date = (p_first and p_first.payment_date) or (b_first and (b_first.bank_remittance_date or b_first.payment_received_date or b_first.scroll_date)) or (r_first and r_first.rbi_credit_date) or b_date or date.today()
            date_token = rec_date.strftime("%Y%m%d")

            # Sequence for IFMS Revenue Transaction ID embedding the automated receipt creation date
            txn_seq = await self.db.execute(text("SELECT ifms_budget.fn_rev_next_seq('REV_TXN_SEQ', 'REV-TXN', :dt)"), {"dt": date_token})
            rev_txn_id = txn_seq.scalar() or f"REV-TXN-{date_token}-{str(recon_idx).zfill(6)}"

            recon_result = RevReconResult(
                rev_transaction_id=rev_txn_id,
                run_id=recon_run.run_id,
                group_key=group_key,
                match_key_type=result_data["match_key_type"],
                challan_no=result_data.get("challan_no"),
                cpin=result_data.get("cpin"),
                cin=result_data.get("cin"),
                revenue_source=result_data["revenue_source"],
                dept_code=result_data["dept_code"],
                pao_code=result_data["pao_code"],
                receipt_head=result_data["receipt_head"],
                payer_name=result_data.get("payer_name"),
                portal_total=result_data["portal_total"],
                bank_total=result_data["bank_total"],
                rbi_total=result_data["rbi_total"],
                amount_difference=result_data["amount_difference"],
                date_variance_days=result_data["date_variance_days"],
                sla_delay_days=result_data["sla_delay_days"],
                penal_interest_amount=result_data["penal_interest_amount"],
                rule_applied=result_data["rule_applied"],
                match_type=result_data["match_type"],
                status=result_data["status"],
                flags=result_data["flags"],
                match_reason=result_data["match_reason"],
                booking_status="READY_FOR_BOOKING" if result_data["status"] == "Matched" else "UNBOOKED",
                machine_status=result_data["status"]
            )
            self.db.add(recon_result)
            await self.db.flush()

            # Create linkages
            for p in group["portal"]:
                self.db.add(RevReconLegLinkage(recon_id=recon_result.recon_id, leg_type="PORTAL", portal_item_id=p.portal_item_id, leg_amount=p.amount, leg_reference_no=p.portal_transaction_id))
            for b in group["bank"]:
                self.db.add(RevReconLegLinkage(recon_id=recon_result.recon_id, leg_type="BANK_SCROLL", scroll_item_id=b.scroll_item_id, leg_amount=b.amount, leg_reference_no=b.bank_reference_no))
            for r in group["rbi"]:
                self.db.add(RevReconLegLinkage(recon_id=recon_result.recon_id, leg_type="RBI_CREDIT", rbi_item_id=r.rbi_item_id, leg_amount=r.amount, leg_reference_no=r.rbi_reference_no))

            # SLA Penal Claim creation if delay observed on bank legs
            if result_data["sla_delay_days"] > 0 and result_data["penal_interest_amount"] > 0 and group["bank"]:
                for b in group["bank"]:
                    b_delay, b_penal = self._calculate_bank_leg_penal(b, penal_rate)
                    if b_delay > 0:
                        claim_seq = await self.db.execute(text("SELECT ifms_budget.fn_rev_next_seq('CLAIM_SEQ', 'SLA-CLM', :dt)"), {"dt": date_token})
                        claim_no = claim_seq.scalar() or f"SLA-CLM-{date_token}-{str(recon_idx).zfill(6)}"

                        # Look up bank_id
                        bank_q = select(RevAgencyBank.bank_id).where(RevAgencyBank.bank_code == b.bank_code)
                        b_id_res = await self.db.execute(bank_q)
                        b_id = b_id_res.scalar() or 1

                        penal_claim = RevPenalClaim(
                            claim_no=claim_no,
                            recon_id=recon_result.recon_id,
                            scroll_item_id=b.scroll_item_id,
                            bank_id=b_id,
                            principal_amount=b.amount,
                            payment_mode=b.payment_mode,
                            base_date=b.payment_received_date,
                            base_date_type="PAYMENT_DATE" if b.payment_mode != "CHEQUE" else "REALISATION_DATE",
                            bank_remittance_date=b.bank_remittance_date,
                            actual_days=(b.bank_remittance_date - b.payment_received_date).days,
                            permitted_days=1,
                            delay_days=b_delay,
                            annual_rate_pct=Decimal(str(penal_rate)),
                            penal_interest_computed=b_penal,
                            penal_interest_recovered=Decimal("0.00"),
                            penal_interest_waived=Decimal("0.00"),
                            penal_interest_outstanding=b_penal,
                            status="COMPUTED"
                        )
                        self.db.add(penal_claim)

            # Create Exception if non-matched
            if result_data["status"] in ["Suspend", "RAT", "Mismatch", "Duplicate", "Under Investigation"]:
                exc_seq = await self.db.execute(text("SELECT ifms_budget.fn_rev_next_seq('EXC_SEQ', 'EXC', :dt)"), {"dt": date_token})
                exc_no = exc_seq.scalar() or f"EXC-{date_token}-{str(recon_idx).zfill(6)}"
                
                cat, sev = self._categorize_exception(result_data["status"], result_data["rule_applied"])
                exc = RevException(
                    exception_no=exc_no,
                    recon_id=recon_result.recon_id,
                    category=cat,
                    severity=sev,
                    status="Open",
                    ownership_type="AGENCY_BANK" if result_data["status"] == "Suspend" else "DEPARTMENT",
                    due_date=b_date + timedelta(days=3),
                    exception_detail=result_data["match_reason"]
                )
                self.db.add(exc)


            # Create Suspense register entry if required
            if result_data["status"] in ["Suspend", "RAT", "Mismatch", "Duplicate"]:
                susp_head_id = config.rat_suspense_head_id if result_data["status"] == "RAT" else config.suspense_head_id
                if not susp_head_id:
                    # Resolve default suspense head
                    susp_q = select(RevSystemConfig.suspense_head_id).where(RevSystemConfig.config_id == 1)
                    susp_head_id = (await self.db.execute(susp_q)).scalar() or 1

                susp_type_map = {
                    "Suspend": "UNRECONCILED_SUSPENSE",
                    "RAT": "RAT_SUSPENSE",
                    "Mismatch": "AMOUNT_MISMATCH_SUSPENSE",
                    "Duplicate": "DUPLICATE_SUSPENSE",
                }
                susp_entry = RevSuspenseRegister(
                    recon_id=recon_result.recon_id,
                    suspense_type=susp_type_map.get(result_data["status"], "UNRECONCILED_SUSPENSE"),
                    suspense_head_id=susp_head_id,
                    amount=result_data["portal_total"] if result_data["status"] != "RAT" else result_data["rbi_total"],
                    ageing_days=0,
                    status="OPEN"
                )
                self.db.add(susp_entry)

            # KPI Aggregations
            st = result_data["status"]
            if st == "Matched":
                matched_cnt += 1
                total_reconciled_amt += result_data["portal_total"]
            elif st == "Pending":
                pending_cnt += 1
            elif st == "Suspend":
                suspend_cnt += 1
            elif st == "RAT":
                rat_cnt += 1
            elif st == "Mismatch":
                mismatch_cnt += 1
            elif st == "Duplicate":
                duplicate_cnt += 1
            elif st == "Under Investigation":
                under_inv_cnt += 1

            total_penal_interest += result_data["penal_interest_amount"]

        recon_run.total_processed = len(grouped_candidates)
        recon_run.matched_count = matched_cnt
        recon_run.pending_count = pending_cnt
        recon_run.suspend_count = suspend_cnt
        recon_run.rat_count = rat_cnt
        recon_run.mismatch_count = mismatch_cnt
        recon_run.duplicate_count = duplicate_cnt
        recon_run.under_investigation_count = under_inv_cnt
        recon_run.total_reconciled_amount = total_reconciled_amt
        recon_run.total_penal_interest = total_penal_interest

        await self.db.commit()
        await self.db.refresh(recon_run)
        return recon_run

    def _group_records(self, portal_recs, bank_recs, rbi_recs) -> Dict[str, Dict[str, list]]:
        groups = {}
        
        def add(k, leg, rec):
            if not k:
                k = "UNLINKED-" + str(id(rec))
            if k not in groups:
                groups[k] = {"portal": [], "bank": [], "rbi": []}
            groups[k][leg].append(rec)

        for p in portal_recs:
            k = p.cin or p.challan_no or p.cpin or p.portal_transaction_id
            add(k, "portal", p)

        for b in bank_recs:
            k = b.cin or b.challan_no or b.cpin or b.bank_reference_no
            add(k, "bank", b)

        for r in rbi_recs:
            k = r.cin or r.challan_no or r.cpin or r.rbi_reference_no
            add(k, "rbi", r)

        return groups

    def _apply_reconciliation_rules(
        self, group: Dict[str, list], amt_tolerance: Decimal, date_tolerance: int, penal_rate: Decimal, b_date: date
    ) -> Dict[str, Any]:
        p_list = group["portal"]
        b_list = group["bank"]
        r_list = group["rbi"]

        p_total = sum([p.amount for p in p_list], Decimal("0.00"))
        b_total = sum([b.amount for b in b_list], Decimal("0.00"))
        r_total = sum([r.amount for r in r_list], Decimal("0.00"))

        p_first = p_list[0] if p_list else None
        b_first = b_list[0] if b_list else None
        r_first = r_list[0] if r_list else None

        source = (p_first and p_first.revenue_source) or (b_first and b_first.revenue_source) or (r_first and r_first.receipt_head[:4]) or "GST"
        dept = (p_first and p_first.dept_code) or (b_first and b_first.dept_code) or "TT"
        pao = (p_first and p_first.pao_code) or (b_first and b_first.pao_code) or "PAO21"
        head = (p_first and p_first.receipt_head) or (b_first and b_first.receipt_head) or (r_first and r_first.receipt_head) or "0040-00-102-01-00-01"
        payer = (p_first and p_first.payer_name) or (b_first and b_first.payer_name) or "Taxpayer"
        challan = (p_first and p_first.challan_no) or (b_first and b_first.challan_no) or (r_first and r_first.challan_no)
        cin = (p_first and p_first.cin) or (b_first and b_first.cin) or (r_first and r_first.cin)
        cpin = (p_first and p_first.cpin) or (b_first and b_first.cpin) or (r_first and r_first.cpin)

        # 1. Compute SLA delay and penal interest dynamically across bank legs
        sla_delay = 0
        penal_amt = Decimal("0.00")
        if b_list:
            for b in b_list:
                d, p_int = self._calculate_bank_leg_penal(b, float(penal_rate))
                sla_delay = max(sla_delay, d)
                penal_amt += p_int

        flags = []
        if sla_delay > 0:
            flags.append("SLA_DELAY_OBSERVED")

        # Attribute Guard (Rule RR-08)
        if p_first and b_first and (p_first.revenue_source != b_first.revenue_source or p_first.dept_code != b_first.dept_code):
            return {
                "match_key_type": "CIN" if cin else "CHALLAN",
                "challan_no": challan, "cpin": cpin, "cin": cin,
                "revenue_source": source, "dept_code": dept, "pao_code": pao, "receipt_head": head, "payer_name": payer,
                "portal_total": p_total, "bank_total": b_total, "rbi_total": r_total,
                "amount_difference": p_total - r_total, "date_variance_days": 0, "sla_delay_days": sla_delay, "penal_interest_amount": penal_amt,
                "rule_applied": "RR-08", "match_type": "Attribute Mismatch", "status": "Under Investigation", "flags": flags + ["ATTRIBUTE_MISMATCH"],
                "match_reason": f"Revenue Source or Department mismatch between Portal ({p_first.revenue_source}/{p_first.dept_code}) and Bank ({b_first.revenue_source}/{b_first.dept_code})."
            }

        # Duplicate scan (Rule RR-05)
        if len(b_list) > 1 and b_total > p_total and p_total > 0:
            return {
                "match_key_type": "CIN" if cin else "CHALLAN",
                "challan_no": challan, "cpin": cpin, "cin": cin,
                "revenue_source": source, "dept_code": dept, "pao_code": pao, "receipt_head": head, "payer_name": payer,
                "portal_total": p_total, "bank_total": b_total, "rbi_total": r_total,
                "amount_difference": p_total - b_total, "date_variance_days": 0, "sla_delay_days": sla_delay, "penal_interest_amount": penal_amt,
                "rule_applied": "RR-05", "match_type": "Duplicate Settlement", "status": "Duplicate", "flags": flags + ["DUPLICATE_SCROLL_LINE"],
                "match_reason": f"Duplicate scroll lines found totaling {b_total}, which exceeds Portal amount {p_total}."
            }

        # RAT / Orphan Credit (Rule RR-04)
        if not p_list and (b_list or r_list):
            return {
                "match_key_type": "CIN" if cin else "CHALLAN",
                "challan_no": challan, "cpin": cpin, "cin": cin,
                "revenue_source": source, "dept_code": dept, "pao_code": pao, "receipt_head": head, "payer_name": payer,
                "portal_total": Decimal("0.00"), "bank_total": b_total, "rbi_total": r_total,
                "amount_difference": Decimal("0.00") - r_total, "date_variance_days": 0, "sla_delay_days": sla_delay, "penal_interest_amount": penal_amt,
                "rule_applied": "RR-04", "match_type": "Orphan Credit", "status": "RAT", "flags": flags + ["RAT_SUSPENSE"],
                "match_reason": "Receipt Awaiting Transfer (RAT): Bank or RBI credit exists without corresponding departmental portal record."
            }

        # Suspend / Missing RBI (Rule RR-03)
        if p_list and not r_list:
            return {
                "match_key_type": "CIN" if cin else "CHALLAN",
                "challan_no": challan, "cpin": cpin, "cin": cin,
                "revenue_source": source, "dept_code": dept, "pao_code": pao, "receipt_head": head, "payer_name": payer,
                "portal_total": p_total, "bank_total": b_total, "rbi_total": Decimal("0.00"),
                "amount_difference": p_total, "date_variance_days": 0, "sla_delay_days": sla_delay, "penal_interest_amount": penal_amt,
                "rule_applied": "RR-03", "match_type": "SLA Ageing Suspend", "status": "Suspend", "flags": flags + ["RBI_CREDIT_MISSING"],
                "match_reason": "Portal receipt exists but RBI government-account credit is missing after permitted remittance SLA."
            }

        # Amount Mismatch (Rule RR-06)
        diff = abs(p_total - r_total)
        if diff > Decimal(str(amt_tolerance)):
            return {
                "match_key_type": "CIN" if cin else "CHALLAN",
                "challan_no": challan, "cpin": cpin, "cin": cin,
                "revenue_source": source, "dept_code": dept, "pao_code": pao, "receipt_head": head, "payer_name": payer,
                "portal_total": p_total, "bank_total": b_total, "rbi_total": r_total,
                "amount_difference": p_total - r_total, "date_variance_days": 0, "sla_delay_days": sla_delay, "penal_interest_amount": penal_amt,
                "rule_applied": "RR-06", "match_type": "Amount Variance", "status": "Mismatch", "flags": flags + ["AMOUNT_MISMATCH"],
                "match_reason": f"Amount difference of ₹{diff} exceeds configured tolerance of ₹{amt_tolerance}."
            }

        # Check Date Variance
        date_variance = 0
        if p_first and r_first:
            date_variance = abs((r_first.rbi_credit_date - p_first.payment_date).days)

        # Split One-to-Many Match (Rule RR-02)
        if len(b_list) > 1 or len(r_list) > 1:
            return {
                "match_key_type": "CIN" if cin else "CHALLAN",
                "challan_no": challan, "cpin": cpin, "cin": cin,
                "revenue_source": source, "dept_code": dept, "pao_code": pao, "receipt_head": head, "payer_name": payer,
                "portal_total": p_total, "bank_total": b_total, "rbi_total": r_total,
                "amount_difference": p_total - r_total, "date_variance_days": date_variance, "sla_delay_days": sla_delay, "penal_interest_amount": penal_amt,
                "rule_applied": "RR-02", "match_type": "One-to-Many", "status": "Matched", "flags": flags,
                "match_reason": f"One-to-Many split settlement matched: 1 Portal txn settled across {len(b_list)} Bank / {len(r_list)} RBI partial credits."
            }

        # Date Variance (Rule RR-07)
        if date_variance > date_tolerance and sla_delay == 0:
            return {
                "match_key_type": "CIN" if cin else "CHALLAN",
                "challan_no": challan, "cpin": cpin, "cin": cin,
                "revenue_source": source, "dept_code": dept, "pao_code": pao, "receipt_head": head, "payer_name": payer,
                "portal_total": p_total, "bank_total": b_total, "rbi_total": r_total,
                "amount_difference": p_total - r_total, "date_variance_days": date_variance, "sla_delay_days": 0, "penal_interest_amount": Decimal("0.00"),
                "rule_applied": "RR-07", "match_type": "Date Variance", "status": "Under Investigation", "flags": ["DATE_VARIANCE"],
                "match_reason": f"Credit date variance of {date_variance} days exceeds tolerance of {date_tolerance} days."
            }

        # Exact 3-Way Match (Rule RR-01)
        return {
            "match_key_type": "CIN" if cin else "CHALLAN",
            "challan_no": challan, "cpin": cpin, "cin": cin,
            "revenue_source": source, "dept_code": dept, "pao_code": pao, "receipt_head": head, "payer_name": payer,
            "portal_total": p_total, "bank_total": b_total, "rbi_total": r_total,
            "amount_difference": p_total - r_total, "date_variance_days": date_variance, "sla_delay_days": sla_delay, "penal_interest_amount": penal_amt,
            "rule_applied": "RR-01", "match_type": "One-to-One", "status": "Matched", "flags": flags,
            "match_reason": "Exact three-way match across Portal, Agency Bank, and RBI government-account credit."
        }

    def _calculate_bank_leg_penal(self, b: RevAgencyBankScrollStaging, penal_rate: float) -> Tuple[int, Decimal]:
        m = (getattr(b, "payment_mode", "") or "").upper()
        is_instrument = (m in ["CHEQUE", "DD"])
        allowed_days = 2 if (is_instrument or m == "CASH") else 1

        base_d = b.payment_received_date
        if is_instrument and hasattr(b, "instrument_realization_date") and b.instrument_realization_date:
            base_d = b.instrument_realization_date

        remit_d = b.bank_remittance_date
        if not base_d or not remit_d:
            return 0, Decimal("0.00")

        actual_days = max(0, (remit_d - base_d).days)
        delay_days = max(0, actual_days - allowed_days)

        if delay_days <= 0 or not b.amount or b.amount <= 0:
            return 0, Decimal("0.00")

        # Simple interest: (Principal * Rate / 100 * Days / 365)
        interest = round((float(b.amount) * (penal_rate / 100.0) * delay_days) / 365.0, 2)
        return delay_days, Decimal(str(interest))

    def _categorize_exception(self, status: str, rule: str) -> Tuple[str, str]:
        if status == "Suspend":
            return "UNREMITTED_BANK_COLLECTION", "Critical"
        elif status == "RAT":
            return "UNIDENTIFIED_GOVT_CREDIT", "High"
        elif status == "Mismatch":
            return "AMOUNT_MISMATCH", "Critical"
        elif status == "Duplicate":
            return "DUPLICATE_SETTLEMENT", "High"
        elif status == "Under Investigation":
            return "DATE_OR_ATTRIBUTE_VARIANCE", "Medium"
        return "GENERAL_EXCEPTION", "Low"

    async def propose_override(self, recon_id: int, proposed_status: str, justification: str, user_id: int) -> RevReconOverride:
        recon = await self.db.get(RevReconResult, recon_id)
        if not recon:
            raise NotFoundException("Recon Result", recon_id)
        
        override = RevReconOverride(
            recon_id=recon_id,
            original_machine_status=recon.status,
            proposed_status=proposed_status,
            proposer_justification=justification,
            proposed_by=user_id,
            proposed_at=datetime.now(),
            decision_status="PENDING_APPROVAL"
        )
        self.db.add(override)
        await self.db.commit()
        await self.db.refresh(override)
        return override

    async def decide_override(self, recon_id: Optional[int], decision: str, remarks: Optional[str], user_id: int, override_id: Optional[int] = None) -> RevReconResult:
        if override_id:
            override = await self.db.get(RevReconOverride, override_id)
            if not override:
                raise NotFoundException("Override Proposal", override_id)
            recon = await self.db.get(RevReconResult, override.recon_id)
            if not recon:
                raise NotFoundException("Recon Result", override.recon_id)
        else:
            recon = await self.db.get(RevReconResult, recon_id)
            if not recon:
                raise NotFoundException("Recon Result", recon_id)

            over_q = (
                select(RevReconOverride)
                .where(RevReconOverride.recon_id == recon_id, RevReconOverride.decision_status == "PENDING_APPROVAL")
                .order_by(RevReconOverride.override_id.desc())
            )
            over_res = await self.db.execute(over_q)
            override = over_res.scalar_one_or_none()

            if not override:
                raise NotFoundException("Pending Override Proposal", recon_id)


        override.decision_status = decision.upper()
        override.checker_user_id = user_id
        override.checker_remarks = remarks
        override.decided_at = datetime.now()

        if decision.upper() == "APPROVED":
            recon.status = override.proposed_status
            recon.is_manual_override = True
            recon.match_reason = f"Manual override approved: {override.proposer_justification}"
            if recon.status == "Matched":
                recon.booking_status = "READY_FOR_BOOKING"

        await self.db.commit()
        await self.db.refresh(recon)
        return recon

    async def trace_result(self, recon_id: int, user_id: int) -> Dict[str, Any]:
        recon = await self.db.get(RevReconResult, recon_id)
        if not recon:
            raise NotFoundException("Recon Result", recon_id)
        
        detail = await self.get_result_detail(recon_id)

        # Log audit entry in AuditChangeLog
        audit_entry = AuditChangeLog(
            schema_name="ifms_budget",
            table_name="rev_recon_result",
            operation="U",
            row_pk=str(recon_id),
            new_data={
                "action": "TRANSACTION_TRACED",
                "traced_by": user_id,
                "status": recon.status,
                "challan_no": recon.challan_no,
                "rev_transaction_id": recon.rev_transaction_id,
                "timestamp": datetime.now().isoformat()
            },
            changed_by=user_id,
            changed_at=datetime.now(),
        )
        self.db.add(audit_entry)
        await self.db.commit()

        return {
            "recon_id": recon.recon_id,
            "rev_transaction_id": recon.rev_transaction_id,
            "status": recon.status,
            "challan_no": recon.challan_no,
            "cin": recon.cin,
            "cpin": recon.cpin,
            "payer_name": recon.payer_name,
            "dept_code": recon.dept_code,
            "pao_code": recon.pao_code,
            "revenue_source": recon.revenue_source,
            "receipt_head": recon.receipt_head,
            "portal_total": float(recon.portal_total),
            "bank_total": float(recon.bank_total),
            "rbi_total": float(recon.rbi_total),
            "amount_difference": float(recon.amount_difference),
            "sla_delay_days": recon.sla_delay_days,
            "penal_interest_amount": float(recon.penal_interest_amount),
            "match_type": recon.match_type,
            "rule_applied": recon.rule_applied,
            "match_reason": recon.match_reason,
            "booking_status": recon.booking_status,
            "is_manual_override": recon.is_manual_override,
            "linkages": detail.get("linkages", []),
            "portal_legs": [detail["portal_details"]] if detail.get("portal_details") else [],
            "bank_legs": detail.get("bank_details", []) or [],
            "rbi_legs": detail.get("rbi_details", []) or [],
            "overrides": detail.get("overrides", []) or [],
            "notes": detail.get("notes", []) or [],
            "traced_at": datetime.now().isoformat(),
            "traced_by": user_id
        }

    async def solve_discrepancy(
        self,
        recon_id: int,
        resolution_type: str,
        target_status: str,
        remarks: str,
        reference_no: Optional[str],
        user_id: int,
        suspense_head_code: Optional[str] = None,
        adjust_amount: Optional[Decimal] = None
    ) -> Dict[str, Any]:
        recon = await self.db.get(RevReconResult, recon_id)
        if not recon:
            raise NotFoundException("Recon Result", recon_id)

        old_status = recon.status
        old_booking = recon.booking_status
        applied_target_status = target_status or ("Matched" if resolution_type == "MANUAL_MATCH" else "Resolved")

        # 1. Update RevReconResult
        recon.status = applied_target_status
        recon.is_manual_override = True
        recon.match_reason = f"Solved ({resolution_type}): {remarks}" + (f" [Ref: {reference_no}]" if reference_no else "")
        if applied_target_status == "Matched":
            recon.booking_status = "READY_FOR_BOOKING"
        elif applied_target_status in ("Suspend", "RAT"):
            recon.booking_status = "UNBOOKED"
        
        recon.updated_by = user_id
        recon.updated_at = datetime.now()

        # 2. Record in RevReconOverride
        override = RevReconOverride(
            recon_id=recon_id,
            original_machine_status=old_status,
            proposed_status=applied_target_status,
            proposer_justification=remarks,
            proposed_by=user_id,
            proposed_at=datetime.now(),
            decision_status="APPROVED",
            checker_user_id=user_id,
            checker_remarks=f"Direct resolution ({resolution_type})" + (f" Ref: {reference_no}" if reference_no else ""),
            decided_at=datetime.now(),
            organization_id=1,
            org_branch_id=1,
            created_by=user_id,
            updated_by=user_id,
            workflow_status="APPROVED"
        )
        self.db.add(override)

        # 3. If resolution involves Suspense, create RevSuspenseRegister entry
        if resolution_type == "POST_TO_SUSPENSE" or applied_target_status == "Suspend":
            susp_coa = None
            if suspense_head_code:
                c_res = await self.db.execute(select(ChartOfAccount).where(ChartOfAccount.coa_code == suspense_head_code))
                susp_coa = c_res.scalar_one_or_none()
            if not susp_coa:
                c_res = await self.db.execute(select(ChartOfAccount).where(ChartOfAccount.coa_code.like("8658%")).limit(1))
                susp_coa = c_res.scalar_one_or_none()
            
            susp_head_id = susp_coa.coa_id if susp_coa else 1
            susp_amount = adjust_amount or (recon.amount_difference if recon.amount_difference != 0 else recon.portal_total)
            if susp_amount <= 0:
                susp_amount = recon.portal_total or recon.rbi_total or Decimal("100.00")

            susp_entry = RevSuspenseRegister(
                recon_id=recon_id,
                suspense_type="UNRECONCILED_SUSPENSE" if old_status == "Suspend" else "AMOUNT_MISMATCH_SUSPENSE",
                suspense_head_id=susp_head_id,
                amount=susp_amount,
                ageing_days=recon.date_variance_days or 0,
                status="OPEN"
            )
            self.db.add(susp_entry)

        # 4. If linked exception exists, close it
        exc_q = select(RevException).where(RevException.recon_id == recon_id, RevException.status != "Closed")
        exc_res = await self.db.execute(exc_q)
        active_exceptions = list(exc_res.scalars().all())
        for exc in active_exceptions:
            exc.status = "Resolved"
            exc.resolution_reason = resolution_type[:150]
            exc.resolution_remarks = f"Discrepancy resolved via {resolution_type}: {remarks}"
            exc.resolved_at = datetime.now()
            exc.resolved_by = user_id
            exc.updated_by = user_id
            
            note = RevExceptionNote(
                exception_id=exc.exception_id,
                created_by=user_id,
                note_text=f"Solved ({resolution_type}): {remarks}" + (f" [Ref: {reference_no}]" if reference_no else ""),
                action_type="RESOLVED"
            )
            self.db.add(note)

        # 5. Record AuditChangeLog
        audit_log = AuditChangeLog(
            schema_name="ifms_budget",
            table_name="rev_recon_result",
            operation="U",
            row_pk=str(recon_id),
            old_data={"status": old_status, "booking_status": old_booking},
            new_data={
                "status": applied_target_status,
                "booking_status": recon.booking_status,
                "resolution_type": resolution_type,
                "remarks": remarks,
                "reference_no": reference_no,
                "resolved_by": user_id
            },
            changed_by=user_id,
            changed_at=datetime.now()
        )
        self.db.add(audit_log)

        # 6. Push SystemNotification
        notif = SystemNotification(
            notification_code=f"NOTIF-SOLVE-{recon_id}-{datetime.now().strftime('%H%M%S')}",
            title=f"Discrepancy Solved: Challan {recon.challan_no or recon.rev_transaction_id}",
            text=f"Record {recon.rev_transaction_id} updated from {old_status} to {applied_target_status} via {resolution_type}. Remarks: {remarks}",
            level="ok",
            target_role="PAO_CHECK",
            action_module="Recon",
            reference_id=str(recon_id),
            is_read=False,
            created_at=datetime.now(),
            created_by=user_id,
            updated_by=user_id,
            workflow_status="ACTIVE"
        )
        self.db.add(notif)

        await self.db.commit()
        await self.db.refresh(recon)

        return {
            "message": f"Discrepancy successfully resolved as {applied_target_status}.",
            "recon_id": recon.recon_id,
            "status": recon.status,
            "booking_status": recon.booking_status,
            "match_reason": recon.match_reason,
            "is_manual_override": recon.is_manual_override,
            "resolved_at": datetime.now().isoformat()
        }

    async def send_discrepancy_letter(
        self,
        recon_id: int,
        recipient_type: str,
        recipient_name: str,
        recipient_address: Optional[str],
        letter_subject: str,
        letter_body: str,
        user_id: int,
        target_role: Optional[str] = "PAO_CHECK"
    ) -> Dict[str, Any]:
        recon = await self.db.get(RevReconResult, recon_id)
        if not recon:
            raise NotFoundException("Recon Result", recon_id)

        # 1. Find or auto-create linked RevException for foreign key integrity
        exc_q = select(RevException).where(RevException.recon_id == recon_id)
        exc_res = await self.db.execute(exc_q)
        exc = exc_res.scalars().first()

        rec_date = recon.created_at.date() if recon.created_at else date.today()
        date_token = rec_date.strftime("%Y%m%d")

        if not exc:
            seq_exc = await self.db.execute(text("SELECT ifms_budget.fn_rev_next_seq('EXC_SEQ', 'EXC', :dt)"), {"dt": date_token})
            exc_no = seq_exc.scalar() or f"EXC-{date_token}-{str(recon_id).zfill(6)}"
            
            sev = "High" if (recon.amount_difference and abs(recon.amount_difference) > Decimal("10000.00")) or recon.status in ["Mismatch", "Duplicate"] else "Medium"
            
            exc = RevException(
                exception_no=exc_no,
                recon_id=recon_id,
                category=recon.status if recon.status in ["Mismatch", "Duplicate", "Suspend", "RAT"] else "Reconciliation Discrepancy",
                severity=sev,
                status="Open",
                ownership_type=recipient_type or "AGENCY_BANK",
                due_date=date.today() + timedelta(days=7),
                exception_detail=f"Discrepancy notice issued for Recon #{recon.recon_id} ({recon.rev_transaction_id}). Challan: {recon.challan_no or 'N/A'}. Status: {recon.status}. Reason: {recon.match_reason}",
                created_by=user_id,
                updated_by=user_id,
                organization_id=1,
                org_branch_id=1,
                workflow_status="ACTIVE"
            )
            self.db.add(exc)
            await self.db.flush()

        # 2. Generate sequential Letter Number embedding the automated receipt date
        seq_ltr = await self.db.execute(text("SELECT ifms_budget.fn_rev_next_seq('LETTER_SEQ', 'LTR-DISC', :dt)"), {"dt": date_token})
        letter_no = seq_ltr.scalar() or f"LTR-DISC-{date_token}-{str(recon_id).zfill(6)}"

        # 3. Create RevExceptionLetter in PostgreSQL
        letter = RevExceptionLetter(
            letter_no=letter_no,
            exception_id=exc.exception_id,
            recipient_type=recipient_type,
            recipient_name=recipient_name,
            recipient_address=recipient_address,
            letter_subject=letter_subject,
            letter_body=letter_body,
            issued_date=date.today(),
            issued_by=user_id,
            status="ISSUED",
            organization_id=1,
            org_branch_id=1,
            created_by=user_id,
            updated_by=user_id,
            workflow_status="ISSUED"
        )
        self.db.add(letter)

        # 4. Create timeline note in RevExceptionNote
        note = RevExceptionNote(
            exception_id=exc.exception_id,
            action_type="LETTER_ISSUED",
            note_text=f"Discrepancy notice {letter_no} issued to {recipient_name} ({recipient_type}). Subject: {letter_subject}",
            created_by=user_id,
            organization_id=1,
            org_branch_id=1,
            workflow_status="ACTIVE"
        )
        self.db.add(note)

        # 5. Record in AuditChangeLog
        audit = AuditChangeLog(
            schema_name="ifms_budget",
            table_name="rev_exception_letter",
            operation="I",
            row_pk=letter_no,
            new_data={
                "letter_no": letter_no,
                "exception_id": exc.exception_id,
                "recon_id": recon_id,
                "recipient_name": recipient_name,
                "recipient_type": recipient_type,
                "subject": letter_subject,
                "issued_by": user_id
            },
            changed_by=user_id,
            changed_at=datetime.now()
        )
        self.db.add(audit)

        # 6. Push SystemNotification
        notif = SystemNotification(
            notification_code=f"NOTIF-LTR-{recon_id}-{datetime.now().strftime('%H%M%S')}",
            title=f"Discrepancy Notice Dispatched: {letter_no}",
            text=f"Official notice {letter_no} issued to {recipient_name} for Challan {recon.challan_no or recon.rev_transaction_id} ({recon.status}).",
            level="info",
            target_role=target_role or "PAO_CHECK",
            action_module="Recon",
            reference_id=str(recon_id),
            is_read=False,
            created_at=datetime.now(),
            created_by=user_id,
            updated_by=user_id,
            workflow_status="ACTIVE"
        )
        self.db.add(notif)

        await self.db.commit()
        await self.db.refresh(letter)

        return {
            "status": "SUCCESS",
            "message": f"Discrepancy letter {letter.letter_no} issued and logged successfully.",
            "letter_id": letter.letter_id,
            "letter_no": letter.letter_no,
            "exception_id": exc.exception_id,
            "exception_no": exc.exception_no,
            "recon_id": recon_id,
            "recipient_type": letter.recipient_type,
            "recipient_name": letter.recipient_name,
            "recipient_address": letter.recipient_address,
            "letter_subject": letter.letter_subject,
            "letter_body": letter.letter_body,
            "issued_date": letter.issued_date.isoformat(),
            "status": letter.status
        }


    async def get_summary(self) -> Dict[str, Any]:
        # 1. Total Staged Portal records
        p_q = select(func.count(RevPortalTransactionStaging.portal_item_id), func.coalesce(func.sum(RevPortalTransactionStaging.amount), Decimal("0.00")))
        p_res = (await self.db.execute(p_q)).first()
        portal_count = p_res[0] or 0
        portal_total = float(p_res[1] or Decimal("0.00"))

        # 2. Total Staged Bank Scroll records
        b_q = select(func.count(RevAgencyBankScrollStaging.scroll_item_id), func.coalesce(func.sum(RevAgencyBankScrollStaging.amount), Decimal("0.00")))
        b_res = (await self.db.execute(b_q)).first()
        bank_count = b_res[0] or 0
        bank_total = float(b_res[1] or Decimal("0.00"))

        # 3. Total Staged RBI Luggage records
        r_q = select(func.count(RevRbiLuggageStaging.rbi_item_id), func.coalesce(func.sum(RevRbiLuggageStaging.amount), Decimal("0.00")))
        r_res = (await self.db.execute(r_q)).first()
        rbi_count = r_res[0] or 0
        rbi_total = float(r_res[1] or Decimal("0.00"))

        # 4. Status aggregations from RevReconResult
        st_q = select(
            RevReconResult.status,
            func.count(RevReconResult.recon_id),
            func.coalesce(func.sum(RevReconResult.portal_total), Decimal("0.00")),
            func.coalesce(func.sum(RevReconResult.bank_total), Decimal("0.00")),
            func.coalesce(func.sum(RevReconResult.rbi_total), Decimal("0.00")),
            func.coalesce(func.sum(func.abs(RevReconResult.amount_difference)), Decimal("0.00")),
            func.coalesce(func.sum(RevReconResult.penal_interest_amount), Decimal("0.00"))
        ).group_by(RevReconResult.status)
        st_res = (await self.db.execute(st_q)).all()

        status_breakdown = {
            "Matched": {"count": 0, "gross_amount": 0.0, "variance_amount": 0.0},
            "Pending": {"count": 0, "gross_amount": 0.0, "variance_amount": 0.0},
            "Suspend": {"count": 0, "gross_amount": 0.0, "variance_amount": 0.0},
            "RAT": {"count": 0, "gross_amount": 0.0, "variance_amount": 0.0},
            "Mismatch": {"count": 0, "gross_amount": 0.0, "variance_amount": 0.0},
            "Duplicate": {"count": 0, "gross_amount": 0.0, "variance_amount": 0.0},
        }
        total_penal = Decimal("0.00")
        for row in st_res:
            st, cnt, p_amt, b_amt, r_amt, diff, penal = row
            status_breakdown[st] = {
                "count": cnt,
                "portal_amount": float(p_amt),
                "bank_amount": float(b_amt),
                "rbi_amount": float(r_amt),
                "gross_amount": float(p_amt if st != "RAT" else r_amt),
                "variance_amount": float(diff if st in ["Mismatch", "Duplicate"] else Decimal("0.00")),
                "penal_amount": float(penal)
            }
            total_penal += penal

        return {
            "control_totals": {
                "portal": {"count": portal_count, "amount": portal_total},
                "bank": {"count": bank_count, "amount": bank_total},
                "rbi": {"count": rbi_count, "amount": rbi_total}
            },
            "status_breakdown": status_breakdown,
            "total_penal_interest": float(total_penal)
        }

    async def reset_reconciliation(self) -> Dict[str, Any]:
        tables = [
            'rev_recon_override',
            'rev_recon_leg_linkage',
            'rev_recon_result',
            'rev_recon_run',
            'rev_penal_waiver',
            'rev_penal_bank_response',
            'rev_penal_letter',
            'rev_penal_claim',
            'rev_exception_note',
            'rev_exception_letter',
            'rev_exception',
            'rev_suspense_register'
        ]
        for t in tables:
            try:
                await self.db.execute(text(f"TRUNCATE TABLE ifms_budget.{t} CASCADE"))
            except Exception:
                await self.db.execute(text(f"DELETE FROM ifms_budget.{t}"))
        await self.db.commit()
        return {"status": "SUCCESS", "message": "Reconciliation ledger reset successfully. Uploaded source data retained."}

class ReconEngine:
    @staticmethod
    async def run_3way_reconciliation(
        db: AsyncSession,
        source_id: Optional[int] = None,
        business_date: Optional[date] = None,
        user_id: int = 1,
    ) -> Dict[str, Any]:
        svc = ReconEngineService(db)
        run = await svc.execute_matching_engine(user_id=user_id, business_date=business_date)
        return {
            "run_id": run.run_id,
            "run_no": run.run_no,
            "total_records": run.total_processed,
            "total_processed": run.total_processed,
            "matched_count": run.matched_count,
            "unmatched_count": run.suspend_count + run.rat_count + run.mismatch_count + run.duplicate_count + run.under_investigation_count,
            "exception_count": run.suspend_count + run.rat_count + run.mismatch_count + run.duplicate_count + run.under_investigation_count,
            "matched_amount": float(run.total_reconciled_amount),
            "penal_interest": float(run.total_penal_interest),
        }

    @staticmethod
    async def get_recon_results(
        db: AsyncSession,
        status: Optional[str] = None,
        source_id: Optional[int] = None,
        match_rule_id: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, Any]:
        svc = ReconEngineService(db)
        page = (offset // limit) + 1
        items, total = await svc.list_results(
            status=status,
            search=search,
            page=page,
            limit=limit
        )
        return {
            "total": total,
            "items": items
        }

    @staticmethod
    async def get_recon_summary(db: AsyncSession) -> Dict[str, Any]:
        svc = ReconEngineService(db)
        return await svc.get_summary()

    @staticmethod
    async def reset_recon_results(db: AsyncSession) -> Dict[str, Any]:
        svc = ReconEngineService(db)
        return await svc.reset_reconciliation()

    @staticmethod
    async def get_recon_detail(db: AsyncSession, recon_id: int) -> Dict[str, Any]:
        svc = ReconEngineService(db)
        return await svc.get_result_detail(recon_id)

    @staticmethod
    async def propose_manual_override(
        db: AsyncSession,
        recon_id: int,
        override_status: str,
        override_reason: str,
        user_id: int,
    ) -> RevReconOverride:
        svc = ReconEngineService(db)
        return await svc.propose_override(recon_id, override_status, override_reason, user_id)

    @staticmethod
    async def approve_manual_override(
        db: AsyncSession,
        recon_id: int,
        approved: bool,
        remarks: Optional[str],
        user_id: int,
    ) -> RevReconResult:
        svc = ReconEngineService(db)
        decision = "APPROVED" if approved else "REJECTED"
        return await svc.decide_override(recon_id, decision, remarks, user_id)

    @staticmethod
    async def trace_recon_result(db: AsyncSession, recon_id: int, user_id: int) -> Dict[str, Any]:
        svc = ReconEngineService(db)
        return await svc.trace_result(recon_id, user_id)

    @staticmethod
    async def solve_recon_discrepancy(
        db: AsyncSession,
        recon_id: int,
        resolution_type: str,
        target_status: str,
        remarks: str,
        reference_no: Optional[str],
        user_id: int,
        suspense_head_code: Optional[str] = None,
        adjust_amount: Optional[Decimal] = None
    ) -> Dict[str, Any]:
        svc = ReconEngineService(db)
        return await svc.solve_discrepancy(
            recon_id, resolution_type, target_status, remarks, reference_no, user_id, suspense_head_code, adjust_amount
        )

    @staticmethod
    async def send_discrepancy_letter(
        db: AsyncSession,
        recon_id: int,
        recipient_type: str,
        recipient_name: str,
        recipient_address: Optional[str],
        letter_subject: str,
        letter_body: str,
        user_id: int,
        target_role: Optional[str] = "PAO_CHECK"
    ) -> Dict[str, Any]:
        svc = ReconEngineService(db)
        return await svc.send_discrepancy_letter(
            recon_id=recon_id,
            recipient_type=recipient_type,
            recipient_name=recipient_name,
            recipient_address=recipient_address,
            letter_subject=letter_subject,
            letter_body=letter_body,
            user_id=user_id,
            target_role=target_role
        )


