
from typing import List

import pandas as pd
from fastapi import HTTPException
from tortoise.exceptions import IntegrityError, DoesNotExist
from tortoise.transactions import in_transaction

from models import TemplateModel
from models.table_converter import Template_Pydantic, TemplateFieldModel, MappingModel, MappingPairModel, DataType, \
    TemplateChannel, TemplateType
from schemas.table_converter import TemplateAddRequest, TemplateFieldAddRequest, MappingAddRequest, \
    TemplateUpdateRequest, TemplateFieldUpdateRequest
from utils.FormulaUtils import apply_formula_to_column, apply_formula_to_row
from utils.stringutils import split_seller_sku


class TableConvertService:
    def __init__(self):
        pass

    async def query_templates(self, limit, offset) -> List[Template_Pydantic]:
        templates = await TemplateModel.all().offset(offset).limit(limit).order_by('channel')
        return templates

    async def add_template(self, body: TemplateAddRequest) -> Template_Pydantic:
        try:
            template = await TemplateModel.create(
                **body.dict(exclude_unset=True)
            )
        except IntegrityError as e:
            raise HTTPException(status_code=400, detail=str(e))
        return template

    async def update_template(self, template_id: int, body: TemplateUpdateRequest) -> Template_Pydantic:
        try:
            template = await TemplateModel.get(id=template_id)
            if template is None:
                raise HTTPException(status_code=404, detail="Template not found")
            template.update_from_dict(body.dict(exclude_unset=True))
            await template.save()
        except IntegrityError as e:
            raise HTTPException(status_code=400, detail=str(e))
        return template

    async def delete_template(self, template_id: int) -> dict:
        try:
            # Delete Template and associated fields, mappings, and pairs
            async with in_transaction():
                template = await TemplateModel.get(id=template_id)
                if template is None:
                    raise HTTPException(status_code=404, detail="Template not found")
                await template.delete()

                # Delete all fields associated with the template
                await TemplateFieldModel.filter(template_id=template_id).delete()

                # Delete all mappings and pairs associated with the template
                mapping_list = await MappingModel.filter(source_template_id=template_id).all()
                mapping_list += await MappingModel.filter(target_template_id=template_id).all()
                mapping_ids = [m.id for m in mapping_list]
                await MappingPairModel.filter(mapping_id__in=mapping_ids).delete()
                await MappingModel.filter(id__in=mapping_ids).delete()
        except IntegrityError as e:
            raise HTTPException(status_code=400, detail=str(e))
        return {"id": template_id}

    async def get_template_channel_list(self):
        return [t.value for t in TemplateChannel]

    async def get_template_type_list(self):
        return [t.value for t in TemplateType]

    async def query_template_fields(self, template_id: int):
        fields = await (TemplateFieldModel
                        .filter(template_id=template_id)
                        .order_by("order_index")
                        .all())
        return fields


    async def add_template_field(
            self, template_id: int,
            body: TemplateFieldAddRequest
    ) -> TemplateFieldModel:
        try:
            field = await TemplateFieldModel.create(
                template_id=template_id,
                **body.dict(exclude_unset=True)
            )
        except IntegrityError as e:
            raise HTTPException(status_code=400, detail=str(e))
        return field

    async def update_template_field(
            self, field_id: int,
            body: TemplateFieldUpdateRequest
    ) -> TemplateFieldModel:
        try:
            field = await TemplateFieldModel.get(id=field_id)
            if field is None:
                raise HTTPException(status_code=404, detail="Field not found")
            field.update_from_dict(body.dict(exclude_unset=True))
            await field.save()
        except IntegrityError as e:
            raise HTTPException(status_code=400, detail=str(e))
        return field

    async def delete_template_field(self, field_id: int) -> dict:
        try:
            async with in_transaction():
                field = await TemplateFieldModel.get(id=field_id)
                if field is None:
                    raise HTTPException(status_code=404, detail="Field not found")
                await field.delete()

                # Delete all pairs associated with the field
                await MappingPairModel.filter(source_field_id=field_id).delete()
                await MappingPairModel.filter(target_field_id=field_id).delete()

        except IntegrityError as e:
            raise HTTPException(status_code=400, detail=str(e))
        return {"id": field_id}


    async def get_field_type_list(self):
        return [t.value for t in DataType]

    async def query_mapping(self, source_template_id: int, target_template_id: int):
        mapping = await MappingModel.filter(
            source_template_id=source_template_id,
            target_template_id=target_template_id
        ).first()
        if mapping is None:
            raise HTTPException(status_code=404, detail="Mapping not found")
        return mapping

    async def query_mapping_pairs(self, mapping_id: int):
        pairs = await MappingPairModel.filter(mapping_id=mapping_id).all()
        return pairs

    async def add_mapping(self, body: MappingAddRequest):
        if len(body.pairs) == 0:
            raise HTTPException(status_code=400, detail="No mapping pairs provided")

        if body.source_template_id == body.target_template_id:
            raise HTTPException(status_code=400, detail="Source and target templates cannot be the same")

        try:
            # Apply transaction to ensure atomicity
            async with in_transaction():
                mapping = await MappingModel.create(
                    **body.dict(exclude_unset=True)
                )
                for pair in body.pairs:
                    await MappingPairModel.create(
                        mapping_id=mapping.id,
                        **pair.dict(exclude_unset=True)
                    )
        except IntegrityError as e:
            raise HTTPException(status_code=400, detail=str(e))
        return {
            "mapping_id": mapping.id
        }

    async def update_mapping(self, mapping_id: int, body: MappingAddRequest):
        try:
            mapping = await MappingModel.get(id=mapping_id)
            if mapping is None:
                raise HTTPException(status_code=404, detail="Mapping not found")
            if len(body.pairs) == 0:
                raise HTTPException(status_code=400, detail="No mapping pairs provided")
            if body.source_template_id == body.target_template_id:
                raise HTTPException(status_code=400, detail="Source and target templates cannot be the same")

            # Apply transaction to ensure atomicity
            async with in_transaction():
                mapping.update_from_dict(body.dict(exclude_unset=True))
                await mapping.save()
                await MappingPairModel.filter(mapping_id=mapping_id).delete()
                for pair in body.pairs:
                    await MappingPairModel.create(
                        mapping_id=mapping.id,
                        **pair.dict(exclude_unset=True)
                    )
        except IntegrityError as e:
            raise HTTPException(status_code=400, detail=str(e))
        return {
            "mapping_id": mapping.id
        }

    async def __apply_formula_to_field(self, ):
        pass

    async def convert_table_column(self, mapping_id, source_df: pd.DataFrame):
        """
        This function applies the formula to the source column and returns the result as a new column in the dataframe.
        :param mapping_id:
        :param source_df:
        :return:

        Note: this function will be deprecated in the future.
        """
        # 1. Load mapping + field pairs
        try:
            mapping = await MappingModel.get(id=mapping_id)
        except DoesNotExist:
            raise HTTPException(status_code=404, detail="Mapping not found")

        pairs = await MappingPairModel.filter(mapping_id=mapping.id)
        if not pairs:
            raise HTTPException(status_code=400, detail="No field pairs for this mapping")

        # 2. Load field name maps
        source_ids = [p.source_field_id for p in pairs]
        target_ids = [p.target_field_id for p in pairs]

        source_fields = await TemplateFieldModel.filter(id__in=source_ids)
        target_fields = await TemplateFieldModel.filter(id__in=target_ids)

        source_map = {f.id: f for f in source_fields}
        target_map = {f.id: f for f in target_fields}

        # 3. Apply formulas or rename
        df = source_df.copy()
        for pair in pairs:
            src_field = source_map[pair.source_field_id]
            tgt_field = target_map[pair.target_field_id]

            src_col = src_field.field_name
            tgt_col = tgt_field.field_name

            if src_col not in df.columns:
                raise HTTPException(status_code=400, detail=f"Missing column: {src_col}")

            if src_field.formula:
                df[tgt_col] = apply_formula_to_column(
                    df, src_col,
                    src_field.formula,
                    allowed_functions= {
                        "split_seller_sku": split_seller_sku
                })
            else:
                df[tgt_col] = df[src_col]
        df_result = df[[f.field_name for f in target_fields if f.field_name in df.columns]]
        return df_result

    async def convert_table(self, mapping_id, source_df: pd.DataFrame):
        # 1. Load mapping + field pairs
        try:
            mapping = await MappingModel.get(id=mapping_id)
        except DoesNotExist:
            raise HTTPException(status_code=404, detail="Mapping not found")

        pairs = await MappingPairModel.filter(mapping_id=mapping.id)
        if not pairs:
            raise HTTPException(status_code=400, detail="No field pairs for this mapping")

        # 2. Load field name maps
        source_ids = [p.source_field_id for p in pairs]
        target_ids = [p.target_field_id for p in pairs]

        source_fields = await TemplateFieldModel.filter(id__in=source_ids)
        target_fields = await TemplateFieldModel.filter(id__in=target_ids)

        source_map = {f.id: f for f in source_fields}
        target_map = {f.id: f for f in target_fields}

        # 3. Apply formulas or rename
        df = source_df.copy()
        for pair in pairs:
            src_field = source_map[pair.source_field_id]
            tgt_field = target_map[pair.target_field_id]
            tgt_col = tgt_field.field_name

            if src_field.formula:
                df[tgt_col] = df.apply(
                    lambda row: apply_formula_to_row(
                        row.to_dict(),
                        src_field.formula,
                        allowed_functions={
                        "split_seller_sku": split_seller_sku
                    }),
                    axis=1
                )
            else:
                src_col = src_field.field_name
                if src_col not in df.columns:
                    raise HTTPException(status_code=400, detail=f"Missing column: {src_col}")
                df[tgt_col] = df[src_col]
        df_result = df[[f.field_name for f in target_fields if f.field_name in df.columns]]
        return df_result



    async def handle_hg_vip_production_conversion(self, source_df: pd.DataFrame):
        pass

