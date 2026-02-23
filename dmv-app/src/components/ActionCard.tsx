import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import CardMedia from '@mui/material/CardMedia';
import Typography from '@mui/material/Typography';
import { CardActions, Button } from '@mui/material';
import { ReactNode } from 'react';
import { ArrowRight } from '@carbon/icons-react';

export interface ActionCardProps {
    title: string;
    body: string;
    buttonLabel: string | ReactNode;
    buttonDisabled?: boolean;
    buttonAction?: () => void;
    imageSrc: string;

}

export default function ActionCard(props: ActionCardProps) {
    return (
        <Card sx={{ maxWidth: 345 }}>
            <CardMedia
                component="img"
                height="140"
                image={props.imageSrc}
                alt=""
            />
            <CardContent>
                <Typography gutterBottom variant="h6" component="div" sx={{ fontWeight: 'normal' }}>
                    {props.title}
                </Typography>
                <Typography variant="body2" sx={{ color: 'text.secondary' }}>
                    {props.body}
                </Typography>
            </CardContent>
            <CardActions>
                <Button
                    disabled={props.buttonDisabled}
                    variant='outlined'
                    onClick={props.buttonAction}
                    endIcon={<ArrowRight />}
                >
                    {props.buttonLabel}
                </Button>
            </CardActions>
        </Card>
    );
}
